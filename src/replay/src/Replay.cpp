#include "EcstaticaReplay.h"
#ifndef E2R_REPLAY_DISABLED
#include "LogSupport/IO/FileSystemIO.h"
#include "RunArtifacts.h"
#endif
#include "ReplayIdentity.h"
#include "Sha256.h"
#include <algorithm>
#include <array>
#include <charconv>
#include <chrono>
#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <map>
#include <memory>
#include <sstream>
#include <string>
#include <unistd.h>
#include <vector>

volatile uint64_t E2R_replay_sequence = 0, E2R_replay_last_checkpoint = 0;
namespace {
namespace fs = std::filesystem;
using Row = std::vector<std::string>;
using Values = std::array<int64_t, 8>;
struct Event {
  uint64_t seq = 0, count = 1, pump = 0;
  std::string kind, detail;
  Values v{};
};
struct Field {
  std::string scope, name;
  int id;
  int64_t value;
};
constexpr const char *eventHeader =
    "seq,repeat,kind,pump,message_or_result,wparam,lparam,cursor_x,cursor_y,"
    "value_5,value_6,value_7,detail\n";
constexpr const char *stateHeader =
    "checkpoint_id,scope,entity_id,field,value\n";
struct Runtime {
  int mode = 0; // 0 off, 1 capture, 2 replay
  bool failed = false, complete = false, compatible = false, finished = false;
  FILE *events = nullptr, *states = nullptr;
  size_t eventBytesWritten = 0, stateBytesWritten = 0;
  std::string metadataBytes, eventBytes, stateBytes;
  fs::path incompleteMarker;
  bool sourceIncomplete = false;
  std::map<std::string, std::string> metadata;
  std::vector<Event> input;
  std::map<uint64_t, std::vector<Field>> checkpoints;
  std::vector<Field> observed;
  size_t cursor = 0;
  uint64_t expanded = 0, seq = 0, pump = 0, checkpoint = 0, stop = 0,
           stopCheckpoint = 0;
  std::vector<uint64_t> pumps;
  replay::Sha256 eventHash;
  std::array<bool, 256> inputHeld{};
  Event clock;
  bool clockPending = false, clockSeen = false;
  void (*hostControl)(void) = nullptr;
  void (*flushDiagnostic)(void) = nullptr;
  E2R_ReplaySampler sampler = nullptr;
  std::chrono::steady_clock::time_point synced =
      std::chrono::steady_clock::now();
} r;
std::string csv(const Row &row) {
  std::string out;
  for (size_t i = 0; i < row.size(); ++i) {
    if (i)
      out += ',';
    auto &field = row[i];
    bool quote = field.find_first_of(",\"\r\n") != std::string::npos;
    if (quote)
      out += '"';
    for (char c : field) {
      out += c;
      if (c == '"')
        out += '"';
    }
    if (quote)
      out += '"';
  }
  return out + '\n';
}
// Strict bounded RFC-4180 records. Only an unterminated final record is
// recoverable.
template <typename Visitor>
void parseRows(const std::string &data, bool recover, Visitor visit,
               bool *truncated = nullptr) {
  Row row;
  std::string field;
  bool quoted = false, closed = false, start = true;
  size_t length = 0;
  for (size_t i = 0; i < data.size(); ++i) {
    char c = data[i];
    if (!c || ++length > 65536)
      throw std::runtime_error("CSV record exceeds limit or contains NUL");
    if (quoted) {
      if (c == '"') {
        if (i + 1 < data.size() && data[i + 1] == '"') {
          field += '"';
          ++i;
        } else {
          quoted = false;
          closed = true;
        }
      } else
        field += c;
      continue;
    }
    if (c == '"' && start) {
      quoted = true;
      start = false;
      continue;
    }
    if (c == ',' || c == '\n' ||
        (c == '\r' && i + 1 < data.size() && data[i + 1] == '\n')) {
      row.push_back(field);
      field.clear();
      start = true;
      closed = false;
      if (c != ',') {
        if (c == '\r')
          ++i;
        visit(row);
        row = {};
        length = 0;
      }
      continue;
    }
    if (closed || c == '"' || c == '\r')
      throw std::runtime_error("invalid CSV quoting");
    field += c;
    start = false;
  }
  if (length) {
    if (!recover)
      throw std::runtime_error("truncated CSV record");
    if (truncated)
      *truncated = true;
  }
}
std::vector<Row> parse(const std::string &data, bool recover) {
  std::vector<Row> rows;
  parseRows(data, recover, [&](Row &row) { rows.push_back(std::move(row)); });
  return rows;
}
int64_t number(const std::string &s) {
  int64_t value = 0;
  auto result = std::from_chars(s.data(), s.data() + s.size(), value);
  if (s.empty() || result.ec != std::errc{} ||
      result.ptr != s.data() + s.size())
    throw std::runtime_error("invalid CSV integer");
  return value;
}
uint64_t positive(const std::string &s) {
  auto n = number(s);
  if (n < 1)
    throw std::runtime_error("invalid positive integer");
  return n;
}
std::string read(const fs::path &path, size_t limit) {
  if (!fs::is_regular_file(fs::symlink_status(path)) ||
      fs::file_size(path) > limit)
    throw std::runtime_error("missing, symlinked or oversized replay file: " +
                             path.string());
  std::ifstream in(path, std::ios::binary);
  std::string data((std::istreambuf_iterator<char>(in)), {});
  if (in.bad() || data.size() > limit)
    throw std::runtime_error("cannot freeze replay file");
  return data;
}
void report(const std::string &message) {
  std::fprintf(stderr, "replay: %s\n", message.c_str());
#ifndef E2R_REPLAY_DISABLED
  E2R_ArtifactsReport(("replay: " + message).c_str());
#endif
}
[[noreturn]] void stop(int code, const std::string &reason) {
  report(reason + " sequence=" + std::to_string(r.seq) +
         " last_matching_checkpoint=" +
         std::to_string(E2R_replay_last_checkpoint));
  if (r.flushDiagnostic)
    r.flushDiagnostic();
  std::fflush(stderr);
  std::fflush(stdout);
  if (code == 76 && std::getenv("E2R_REPLAY_PAUSE"))
    std::raise(SIGSTOP);
  std::_Exit(code);
}
void fail(const std::string &reason) {
  if (!r.failed) {
    r.failed = true;
    report("RECORDING INCOMPLETE: " + reason);
  }
}
void write(FILE *f, const std::string &bytes) {
  if (r.failed)
    return;
  size_t *written = f == r.events
                        ? &r.eventBytesWritten
                        : (f == r.states ? &r.stateBytesWritten : nullptr);
  if (written) {
    constexpr size_t limit = 256u * 1024u * 1024u;
    if (bytes.size() > limit - *written) {
      fail("capture file limit reached; retained prefix remains replayable");
      return;
    }
    *written += bytes.size();
  }
  if (!f || std::fwrite(bytes.data(), 1, bytes.size(), f) != bytes.size())
    fail("write failed (gameplay continues)");
}
void flush(bool sync = false) {
  for (FILE *f : {r.states, r.events})
    if (f) {
      if (std::fflush(f))
        fail("flush failed");
#ifndef E2R_REPLAY_DISABLED
      if (sync &&
          !Ecstatica::Recompiled::LogSupport::IO::FileSystemIO::SyncFile(f))
        fail("sync failed");
#else
      (void)sync;
#endif
    }
}
void raw(const Event &e) {
  Row row{std::to_string(e.seq), std::to_string(e.count), e.kind,
          std::to_string(e.pump)};
  for (auto n : e.v)
    row.push_back(std::to_string(n));
  row.push_back(e.detail);
  auto bytes = csv(row);
  write(r.events, bytes);
  r.eventHash.add(bytes);
}
void clockFlush() {
  if (r.clockPending) {
    raw(r.clock);
    r.clockPending = false;
  }
}
void emit(const std::string &kind, Values v = {},
          const std::string &detail = "") {
  clockFlush();
  Event e;
  e.seq = ++r.seq;
  e.kind = kind;
  e.pump = r.pumps.empty() ? 0 : r.pumps.back();
  e.v = v;
  e.detail = detail;
  raw(e);
  E2R_replay_sequence = r.seq;
}
const Event &next() {
  if (r.cursor >= r.input.size())
    stop(75, "INCOMPLETE: recovered prefix exhausted");
  const auto &e = r.input[r.cursor];
  if ((r.stop && e.seq + r.expanded >= r.stop) ||
      (r.stopCheckpoint && e.kind == "checkpoint" &&
       uint64_t(e.v[0]) >= r.stopCheckpoint))
    stop(76, "stopped before requested boundary");
  if (e.kind == "end") {
    r.seq = e.seq;
    E2R_replay_sequence = r.seq;
    stop(r.complete ? 0 : 75,
         r.complete ? "MATCHED: clean recording completed"
                    : "INCOMPLETE: completion was not durably published");
  }
  return e;
}
Event consume(const std::string &kind) {
  auto e = next();
  r.seq = e.seq + r.expanded;
  E2R_replay_sequence = r.seq;
  if (e.kind != kind)
    stop(74, "DIVERGED: expected " + e.kind + " actual " + kind);
  r.seq = e.seq + r.expanded;
  E2R_replay_sequence = r.seq;
  if (++r.expanded == e.count) {
    r.expanded = 0;
    ++r.cursor;
  }
  return e;
}
void checkpoint() {
  if (!r.sampler || r.failed)
    return;
  // Pre-input, outermost host-pump boundary; never claims completed simulation.
  r.observed.clear();
  r.sampler();
  uint64_t id = ++r.checkpoint;
  std::string bytes;
  for (const auto &f : r.observed)
    bytes += csv({std::to_string(id), f.scope, std::to_string(f.id), f.name,
                  std::to_string(f.value)});
  auto signature = replay::hash(bytes);
  if (r.mode == 1) {
    write(r.states, bytes);
    if (r.states && std::fflush(r.states))
      fail("checkpoint flush failed");
    emit("checkpoint", {int64_t(id), int64_t(r.observed.size())}, signature);
  } else {
    auto e = consume("checkpoint");
    auto it = r.checkpoints.find(id);
    if (e.v[0] != int64_t(id) || it == r.checkpoints.end())
      stop(74, "DIVERGED: checkpoint identity");
    const auto &expected = it->second;
    for (size_t i = 0; i < expected.size() || i < r.observed.size(); ++i) {
      if (i >= expected.size() || i >= r.observed.size())
        stop(74, "DIVERGED: checkpoint field count");
      const auto &a = expected[i];
      const auto &b = r.observed[i];
      if (a.scope != b.scope || a.id != b.id || a.name != b.name ||
          a.value != b.value)
        stop(74, "DIVERGED: " + a.scope + "[" + std::to_string(a.id) + "]." +
                     a.name + " expected=" + std::to_string(a.value) +
                     " actual=" + b.scope + "[" + std::to_string(b.id) + "]." +
                     b.name + "=" + std::to_string(b.value));
    }
    if (e.detail != signature)
      stop(74, "DIVERGED: checkpoint signature");
  }
  E2R_replay_last_checkpoint = id;
}
void validate() {
  auto meta = parse(r.metadataBytes, false);
  if (meta.empty() || meta[0] != Row{"key", "value"})
    throw std::runtime_error("metadata header");
  for (size_t i = 1; i < meta.size(); ++i)
    if (meta[i].size() != 2 ||
        !r.metadata.emplace(meta[i][0], meta[i][1]).second)
      throw std::runtime_error("duplicate/invalid metadata");
  for (const char *key : {"schema", "executable_sha256", "revision", "backend",
                          "asan", "build", "startup", "game_executable_sha256",
                          "recording_id", "wall_utc", "argument.0"})
    if (!r.metadata.count(key))
      throw std::runtime_error(std::string("missing metadata ") + key);
  if (r.metadata["argument.0"] != "--run-recon")
    throw std::runtime_error("unsupported startup command");
  if (r.metadata["schema"] != "e2replay.csv.1")
    throw std::runtime_error("unsupported replay schema");
  size_t stateRow = 0;
  parseRows(r.stateBytes, true, [&](Row &row) {
    if (stateRow++ == 0) {
      if (csv(row) != stateHeader) throw std::runtime_error("checkpoint header");
      return;
    }
    if (row.size() != 5) throw std::runtime_error("checkpoint columns");
    auto id = positive(row[0]);
    auto entity = number(row[2]);
    if (entity < INT32_MIN || entity > INT32_MAX)
      throw std::runtime_error("entity range");
    r.checkpoints[id].push_back({std::move(row[1]), std::move(row[3]), int(entity), number(row[4])});
  });
  if (!stateRow) throw std::runtime_error("checkpoint header");
  std::string().swap(r.stateBytes);
  bool truncated = false;
  size_t eventRow = 0;
  // Avoid both a complete vector of CSV strings and repeated reallocations of
  // millions of events in the i386 address space. Event fields remain owned.
  r.input.reserve(std::count(r.eventBytes.begin(), r.eventBytes.end(), '\n'));
  replay::Sha256 eventHash;
  eventHash.add(eventHeader);
  uint64_t seq = 1, cp = 0;
  std::vector<uint64_t> pumps;
  uint64_t pump = 0;
  const std::vector<std::string> kinds = {
      "clock", "localtime",  "pump_begin", "pump_end",   "input", "queued",
      "sleep", "cursor_set", "cursor_get", "checkpoint", "end"};
  parseRows(r.eventBytes, true, [&](Row &row) {
    if (eventRow++ == 0) {
      if (csv(row) != eventHeader) throw std::runtime_error("event header");
      return;
    }
    if (r.complete) throw std::runtime_error("invalid completion marker");
    if (row.size() != 13)
      throw std::runtime_error("event columns");
    Event e;
    e.seq = positive(row[0]);
    e.count = positive(row[1]);
    e.kind = row[2];
    auto p = number(row[3]);
    if (p < 0)
      throw std::runtime_error("pump range");
    e.pump = p;
    if (std::find(kinds.begin(), kinds.end(), e.kind) == kinds.end())
      throw std::runtime_error("unknown event kind");
    if (e.seq != seq || e.count > 65536 ||
        (e.kind != "clock" && e.count != 1) || seq > INT64_MAX - e.count)
      throw std::runtime_error("sequence/count discontinuity");
    seq += e.count;
    for (int j = 0; j < 8; ++j)
      e.v[j] = number(row[4 + j]);
    e.detail = row[12];
    if (e.kind == "pump_begin") {
      if (e.pump != ++pump)
        throw std::runtime_error("pump identity");
      pumps.push_back(pump);
    }
    if (e.pump != (pumps.empty() ? 0 : pumps.back()))
      throw std::runtime_error("pump nesting");
    if (e.kind == "pump_end") {
      if (pumps.empty())
        throw std::runtime_error("pump underflow");
      pumps.pop_back();
    }
    if (e.kind == "localtime")
      for (auto value : e.v)
        if (value < 0 || value > 65535)
          throw std::runtime_error("localtime range");
    if (e.kind == "clock" && (e.v[0] < 0 || uint64_t(e.v[0]) > UINT32_MAX))
      throw std::runtime_error("clock range");
    if (e.kind == "input" && (pumps.empty() || e.v[0] < 0 || e.v[0] > 65535 ||
                              e.v[1] < 0 || uint64_t(e.v[1]) > UINT32_MAX ||
                              e.v[2] < INT32_MIN || e.v[2] > UINT32_MAX))
      throw std::runtime_error("input range");
    if (e.kind == "checkpoint") {
      auto id = ++cp;
      auto it = r.checkpoints.find(id);
      if (e.v[0] != int64_t(id) || it == r.checkpoints.end() ||
          int64_t(it->second.size()) != e.v[1])
        throw std::runtime_error("missing checkpoint fields");
      std::string bytes;
      for (const auto &f : it->second)
        bytes += csv({std::to_string(id), f.scope, std::to_string(f.id), f.name,
                      std::to_string(f.value)});
      if (replay::hash(bytes) != e.detail)
        throw std::runtime_error("checkpoint checksum mismatch");
    }
    if (e.kind == "end") {
      if (e.v[0] != int64_t(cp))
        throw std::runtime_error("invalid completion marker");
      if (e.detail != eventHash.finish())
        throw std::runtime_error("event checksum mismatch");
      r.complete = true;
    }
    eventHash.add(csv(row));
    r.input.push_back(std::move(e));
  }, &truncated);
  if (!eventRow) throw std::runtime_error("event header");
  if (r.complete && truncated) throw std::runtime_error("invalid completion marker");
  std::string().swap(r.eventBytes);
  if (r.input.empty())
    throw std::runtime_error("no recoverable events");
}
std::map<std::string, std::string> identity(const char *game, int argc,
                                            char **argv) {
  std::map<std::string, std::string> m;
  m["schema"] = "e2replay.csv.1";
  m["executable_sha256"] = replay::fileHash("/proc/self/exe");
  m["revision"] = E2R_REPLAY_REVISION;
  m["backend"] = E2R_REPLAY_BACKEND;
#ifdef E2R_REPLAY_ASAN
  m["asan"] = "1";
#else
  m["asan"] = "0";
#endif
#ifdef NDEBUG
  m["build"] = "release";
#else
  m["build"] = "debug";
#endif
  m["rng_initial_fallback"] = "0x2a13f00d";
  m["logical_window"] = "1:main";
  m["startup"] = "fresh-process-no-savestate";
  m["game_data_path"] = fs::canonical(game).string();
  // Fixed installation, no asset copies or full archive rehash on each launch.
  m["game_executable_sha256"] =
      replay::fileHash(fs::path(game) / "E2WIN95.EXE");
  for (const auto &p : fs::directory_iterator(fs::path(game) / "Files"))
    if (p.is_regular_file())
      m["asset_size." + p.path().filename().string()] =
          std::to_string(p.file_size());
  for (const char *name : {"e_config", "E_CONFIG"})
    if (fs::exists(fs::path(game) / name))
      m["settings." + std::string(name)] =
          replay::fileHash(fs::path(game) / name);
  for (char **p = ::environ; *p; ++p) {
    std::string entry = *p;
    auto eq = entry.find('=');
    auto name = entry.substr(0, eq);
    if ((name.starts_with("E2R_") && !name.starts_with("E2R_REPLAY") &&
         name != "E2R_RECORD" && name != "E2R_DATA_DIR" &&
         !name.starts_with("E2R_LOG") && !name.starts_with("E2R_INSPECT")) ||
        name == "SDL_VIDEODRIVER" || name == "SDL_AUDIODRIVER" ||
        name == "ASAN_OPTIONS" || name == "TZ")
      m["env." + name] = entry.substr(eq + 1);
  }
  for (int i = 0; i < argc; ++i)
    m["argument." + std::to_string(i)] = argv[i];
  return m;
}
} // namespace
extern "C" int E2R_ReplayPrepare(const char *path) {
  if (!path || !*path)
    return 1;
  try {
    fs::path directory = fs::absolute(path);
    if (directory.filename() == "events.csv")
      directory = directory.parent_path();
#ifndef E2R_REPLAY_DISABLED
    std::unique_ptr<void, decltype(&E2R_ArtifactsUnlockSource)> lock(
        E2R_ArtifactsLockSource(directory.c_str()), E2R_ArtifactsUnlockSource);
    if (!lock)
      throw std::runtime_error(
          "cannot protect replay source (missing or active session)");
#endif
    r.sourceIncomplete = fs::exists(directory / "recording.incomplete");
    r.metadataBytes = read(directory / "metadata.csv", 1024 * 1024);
    r.eventBytes = read(directory / "events.csv", 256 * 1024 * 1024);
    r.stateBytes = read(directory / "checkpoints.csv", 256 * 1024 * 1024);
    validate();
    if (r.sourceIncomplete)
      r.complete = false;
    report(std::string("prepared immutable ") +
           (r.complete ? "complete" : "INCOMPLETE recovered-prefix") +
           " input");
    return 1;
  } catch (const std::exception &e) {
    report(std::string("REJECTED: ") + e.what());
    return 0;
  }
}
extern "C" int E2R_ReplayStart(const char *record, int gameplay,
                               const char *session, const char *game, int argc,
                               char **argv, int compatible, uint64_t stopSeq,
                               uint64_t stopCp, E2R_ReplaySampler sampler) {
  try {
    if (r.input.empty() &&
        (!gameplay || !record || std::string(record) == "off"))
      return 1;
    auto current = identity(game, argc, argv);
    r.sampler = sampler;
    r.stop = stopSeq;
    r.stopCheckpoint = stopCp;
    if (!r.input.empty()) {
      r.mode = 2;
      r.compatible = compatible;
      for (const auto &[key, value] : r.metadata) {
        bool exactOnly = key == "executable_sha256" || key == "revision" ||
                         key == "asan" || key == "build";
        bool descriptive = key == "recording_id" || key == "wall_utc" ||
                           key == "game_data_path" ||
                           key.starts_with("argument.");
        if (!descriptive && (!exactOnly || !compatible) &&
            current[key] != value)
          throw std::runtime_error("incompatible startup field " + key +
                                   " expected=" + value +
                                   " actual=" + current[key]);
      }
      for (const auto &[key, value] : current)
        if (key.starts_with("env.") && !r.metadata.count(key))
          throw std::runtime_error("extra startup environment " + key);
      report(compatible ? "COMPATIBLE attempt: executable differences "
                          "permitted, checkpoints remain strict"
                        : "exact replay started");
    } else {
      if (std::string(E2R_REPLAY_BACKEND) != "sdl") {
        report("capture disabled: SDL fidelity only");
        return 1;
      }
      r.mode = 1;
      auto dir = fs::path(session) / "replay";
      if (!fs::create_directory(dir))
        throw std::runtime_error("replay directory exists");
      r.incompleteMarker = dir / "recording.incomplete";
      {
        std::ofstream marker(r.incompleteMarker);
        marker << "Capture active, interrupted, or failed. Only successful "
                  "final sync removes this marker.\n";
        marker.close();
        if (!marker)
          throw std::runtime_error("cannot publish capture status");
      }
      auto now = std::time(nullptr);
      std::tm utc{};
      gmtime_r(&now, &utc);
      char stamp[32];
      std::strftime(stamp, sizeof stamp, "%Y-%m-%dT%H:%M:%SZ", &utc);
      current["wall_utc"] = stamp;
      current["recording_id"] = fs::path(session).filename().string();
      FILE *meta = std::fopen((dir / "metadata.csv").c_str(), "wb");
      if (!meta)
        throw std::runtime_error("cannot write metadata");
      write(meta, "key,value\n");
      for (auto &[k, v] : current)
        write(meta, csv({k, v}));
      if (std::fclose(meta))
        fail("metadata close failed");
      r.events = std::fopen((dir / "events.csv").c_str(), "wb");
      r.states = std::fopen((dir / "checkpoints.csv").c_str(), "wb");
      write(r.events, eventHeader);
      r.eventHash.add(eventHeader);
      write(r.states, stateHeader);
      flush(true);
      report("recording " + dir.string());
    }
    return 1;
  } catch (const std::exception &e) {
    if (!r.input.empty()) {
      report(std::string("REJECTED: ") + e.what());
      r.mode = 0;
      return 0;
    }
    fail(e.what());
    return 1;
  }
}
extern "C" void E2R_ReplaySetHostControl(void (*poll)(void),
                                         void (*flush)(void)) {
  r.hostControl = poll;
  r.flushDiagnostic = flush;
}
extern "C" int E2R_ReplayPlaying(void) { return r.mode == 2; }
extern "C" int E2R_ReplayCaptureIncomplete(void) { return r.failed; }
extern "C" void E2R_ReplayAbort(void) {
  if (r.mode == 2)
    stop(77, "ABORTED by host control");
}
extern "C" void E2R_ReplayField(const char *scope, int id, const char *name,
                                int64_t value) {
  r.observed.push_back({scope, name, id, value});
}
extern "C" uint32_t E2R_ReplayClock(uint32_t value) {
  if (r.mode == 2) {
    // Poll loops can contain hundreds of millions of identical clock calls.
    // Expand in place: copying Event strings here dominates playback cost.
    if (r.cursor >= r.input.size())
      stop(75, "INCOMPLETE: clock prefix exhausted");
    if ((r.seq & 65535) == 0 && r.hostControl)
      r.hostControl();
    const Event &e = r.input[r.cursor];
    if (e.kind != "clock")
      return uint32_t(consume("clock").v[0]);
    if (r.stop && e.seq + r.expanded >= r.stop)
      stop(76, "stopped before requested clock call");
    r.seq = e.seq + r.expanded;
    E2R_replay_sequence = r.seq;
    uint32_t result = uint32_t(e.v[0]);
    if (++r.expanded == e.count) {
      r.expanded = 0;
      ++r.cursor;
    }
    return result;
  }
  if (r.mode != 1 || r.failed)
    return value;
  const bool newTimestamp = !r.clockSeen || r.clock.v[0] != value;
  r.clockSeen = true;
  if (r.clockPending && (r.clock.v[0] != value || r.clock.count >= 65536))
    clockFlush();
  if (!r.clockPending) {
    r.clock = {};
    r.clock.seq = r.seq + 1;
    r.clock.kind = "clock";
    r.clock.pump = r.pumps.empty() ? 0 : r.pumps.back();
    r.clock.v[0] = value;
    r.clock.count = 0;
    r.clockPending = true;
  }
  ++r.clock.count;
  E2R_replay_sequence = ++r.seq;
  if (newTimestamp) {
    // The first changed result may release the game's busy-wait straight into
    // a faulting update. Publish it before returning, without waiting for the
    // next pump or a shutdown handler. Equal-result suffixes remain compressed.
    clockFlush();
    flush();
  }
  return value;
}
extern "C" void E2R_ReplayLocalTime(uint16_t fields[8]) {
  if (r.mode == 2) {
    auto e = consume("localtime");
    for (int i = 0; i < 8; ++i)
      fields[i] = uint16_t(e.v[i]);
  } else if (r.mode == 1) {
    Values v;
    for (int i = 0; i < 8; ++i)
      v[i] = fields[i];
    emit("localtime", v);
  }
}
extern "C" void E2R_ReplayPumpBegin(void) {
  if (!r.mode || r.failed)
    return;
  ++r.pump;
  r.pumps.push_back(r.pump);
  if (r.mode == 1)
    emit("pump_begin");
  else {
    auto e = consume("pump_begin");
    if (e.pump != r.pump)
      stop(74, "DIVERGED: pump ordinal");
  }
  if (r.pumps.size() == 1 && (r.pump == 1 || r.pump % 1024 == 0))
    checkpoint();
}
extern "C" void E2R_ReplayPumpInputs(E2R_ReplayDelivery deliver) {
  if (r.mode != 2)
    return;
  while (next().kind == "input" || next().kind == "checkpoint") {
    if (next().kind == "checkpoint") {
      checkpoint();
      continue;
    }
    auto e = consume("input");
    if (e.pump != r.pumps.back())
      stop(74, "DIVERGED: input pump");
    deliver(unsigned(e.v[0]), uintptr_t(e.v[1]), intptr_t(e.v[2]));
  }
}
extern "C" void E2R_ReplayPumpEnd(void) {
  if (!r.mode || r.failed)
    return;
  if (r.mode == 1) {
    emit("pump_end");
    auto now = std::chrono::steady_clock::now();
    bool sync = now - r.synced > std::chrono::seconds(1);
    flush(sync);
    if (sync)
      r.synced = now;
  } else {
    auto e = consume("pump_end");
    if (e.pump != r.pumps.back())
      stop(74, "DIVERGED: pump nesting");
  }
  r.pumps.pop_back();
}
extern "C" void E2R_ReplayInput(unsigned msg, uintptr_t key, intptr_t lp, int x,
                                int y) {
  if (r.mode == 1 && !r.failed) {
    bool observe =
        msg !=
        0x200; // mouse motion stays lossless, without full snapshots per pixel
    if ((msg == 0x100 || msg == 0x101) && key < r.inputHeld.size()) {
      bool down = msg == 0x100;
      observe = r.inputHeld[key] != down;
      r.inputHeld[key] = down;
    }
    if (observe)
      checkpoint();
    emit("input", {msg, int64_t(key), int64_t(lp), x, y});
  }
}
extern "C" void E2R_ReplayQueued(unsigned msg, uintptr_t key, intptr_t lp) {
  if (!r.mode || r.failed)
    return;
  Values v{msg, int64_t(key), int64_t(lp)};
  if (r.mode == 1)
    emit("queued", v);
  else {
    auto e = consume("queued");
    if (e.v != v)
      stop(74, "DIVERGED: queued delivery");
  }
}
extern "C" void E2R_ReplayService(const char *kind, int64_t a, int64_t b) {
  if (!r.mode || r.failed)
    return;
  Values v{a, b};
  if (r.mode == 1)
    emit(kind, v);
  else if (consume(kind).v != v)
    stop(74, std::string("DIVERGED: service ") + kind);
}
extern "C" void E2R_ReplayFinish(void) {
  if (r.finished)
    return;
  r.finished = true;
  if (r.mode == 1 && !r.failed) {
    clockFlush();
    flush(true);
    if (!r.failed) {
      emit("end", {int64_t(r.checkpoint)}, r.eventHash.finish());
      flush(true);
    }
  } else if (r.mode == 2) {
    if (next().kind != "end")
      stop(74, "DIVERGED: game exited before recording end");
  }
  for (FILE *file : {r.events, r.states})
    if (file && std::fclose(file))
      fail("close failed");
  r.events = r.states = nullptr;
  if (r.mode == 1 && !r.failed) {
    std::error_code error;
    fs::remove(r.incompleteMarker, error);
    if (error)
      fail("cannot publish clean completion");
  }
  r.mode = 0;
}
