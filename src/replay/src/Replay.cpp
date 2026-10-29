#include "EcstaticaReplay.h"
#ifndef E2R_REPLAY_DISABLED
#include "RunArtifacts.h"
#endif
#include "ReplayIdentity.h"
#include "Sha256.h"
#include "ReplayStorage.h"
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
  replay::ChunkWriter events, states;
  replay::File manifest{nullptr, std::fclose};
  replay::File eventSpool{nullptr, std::fclose}, stateSpool{nullptr, std::fclose};
  std::unique_ptr<replay::CsvReader> eventReader, stateReader;
  std::string metadataBytes;
  bool prepared = false, eventTruncated = false;
  fs::path incompleteMarker;
  bool sourceIncomplete = false;
  std::map<std::string, std::string> metadata;
  Event input;
  bool inputReady = false;
  std::vector<Field> observed;
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
  if (!r.failed)
    try {
      replay::put(f, bytes);
    } catch (const std::exception &e) {
      fail(e.what());
    }
}
void write(replay::ChunkWriter &file, const std::string &bytes) {
  if (!r.failed)
    try {
      file.write(bytes);
    } catch (const std::exception &e) {
      fail(e.what());
    }
}
void flush(bool sync = false) {
  try {
    r.states.flush(sync);
    r.events.flush(sync);
  } catch (const std::exception &e) {
    fail(e.what());
  }
}
Event event(const Row &row) {
  if (row.size() != 13)
    throw std::runtime_error("event columns");
  Event e;
  e.seq = positive(row[0]);
  e.count = positive(row[1]);
  e.kind = row[2];
  auto pump = number(row[3]);
  if (pump < 0)
    throw std::runtime_error("pump range");
  e.pump = pump;
  for (int j = 0; j < 8; ++j)
    e.v[j] = number(row[4 + j]);
  e.detail = row[12];
  return e;
}
const Event &pending() {
  if (!r.inputReady) {
    Row row;
    try {
      if (!r.eventReader->next(row))
        stop(75, "INCOMPLETE: recovered prefix exhausted");
      r.input = event(row);
      r.inputReady = true;
    } catch (const std::exception &e) {
      stop(73, std::string("REJECTED: immutable replay read: ") + e.what());
    }
  }
  return r.input;
}
void advance(const Event &e) {
  if (++r.expanded == e.count) {
    r.expanded = 0;
    r.inputReady = false;
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
  const auto &e = pending();
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
  advance(e);
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
    for (const auto &f : r.observed)
      write(r.states, csv({std::to_string(id), f.scope, std::to_string(f.id),
                           f.name, std::to_string(f.value)}));
    try {
      r.states.flush(false);
    } catch (const std::exception &e) {
      fail(e.what());
    }
    emit("checkpoint", {int64_t(id), int64_t(r.observed.size())}, signature);
  } else {
    auto e = consume("checkpoint");
    if (e.v[0] != int64_t(id) || e.v[1] != int64_t(r.observed.size()))
      stop(74, "DIVERGED: checkpoint identity/field count");
    for (const auto &b : r.observed) {
      Row row;
      try {
        if (!r.stateReader->next(row) || positive(row[0]) != id)
          stop(74, "DIVERGED: checkpoint identity");
      } catch (const std::exception &error) {
        stop(73, std::string("REJECTED: immutable state read: ") + error.what());
      }
      Field a{row[1], row[3], int(number(row[2])), number(row[4])};
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
void validateMetadata() {
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
}

// Freeze to anonymous disk spools while holding the source lease. Retention can
// delete the original after preparation; playback never reopens mutable input.
void freezeChunk(const fs::path &path, FILE *spool, const char *header,
                 bool recover, const std::string &checksum = "",
                 uint64_t size = 0, bool *truncated = nullptr) {
  if (!fs::is_regular_file(fs::symlink_status(path)) ||
      (!checksum.empty() && fs::file_size(path) != size))
    throw std::runtime_error("missing, symlinked or resized replay chunk: " + path.string());
  replay::File file(std::fopen(path.c_str(), "rb"), std::fclose);
  if (!file)
    throw std::runtime_error("cannot open replay chunk");
  replay::CsvReader reader(file.get());
  Row row;
  if (!reader.next(row, recover)) {
    if (!recover)
      throw std::runtime_error("replay chunk header: " + path.string());
    if (truncated)
      *truncated = reader.truncated;
    return; // Rotation may have created a tail before publishing its header.
  }
  if (csv(row) != header)
    throw std::runtime_error("replay chunk header: " + path.string());
  while (reader.next(row, recover))
    replay::put(spool, csv(row));
  if (!checksum.empty() && reader.checksum() != checksum)
    throw std::runtime_error("replay chunk checksum mismatch: " + path.string());
  if (truncated)
    *truncated = reader.truncated;
}
void rewindInput() {
  for (FILE *file : {r.eventSpool.get(), r.stateSpool.get()}) {
    if (std::fflush(file) || ::fseeko(file, 0, SEEK_SET))
      throw std::runtime_error("cannot rewind immutable replay spool");
  }
  r.eventReader = std::make_unique<replay::CsvReader>(r.eventSpool.get());
  r.stateReader = std::make_unique<replay::CsvReader>(r.stateSpool.get());
  Row header;
  if (!r.eventReader->next(header) || csv(header) != eventHeader ||
      !r.stateReader->next(header) || csv(header) != stateHeader)
    throw std::runtime_error("immutable replay header");
}
void freeze(const fs::path &directory) {
  r.eventSpool = replay::temporary();
  r.stateSpool = replay::temporary();
  replay::put(r.eventSpool.get(), eventHeader);
  replay::put(r.stateSpool.get(), stateHeader);
  if (!r.metadata.count("storage")) {
    freezeChunk(directory / "events.csv", r.eventSpool.get(), eventHeader,
                true, "", 0, &r.eventTruncated);
    freezeChunk(directory / "checkpoints.csv", r.stateSpool.get(), stateHeader, true);
  } else {
    if (r.metadata.at("storage") != "chunked.csv.1")
      throw std::runtime_error("unsupported replay storage");
    auto path = directory / "chunks.csv";
    if (!fs::is_regular_file(fs::symlink_status(path)))
      throw std::runtime_error("missing or symlinked replay manifest");
    replay::File file(std::fopen(path.c_str(), "rb"), std::fclose);
    if (!file)
      throw std::runtime_error("cannot open replay manifest");
    replay::CsvReader manifest(file.get());
    Row row;
    if (!manifest.next(row) || csv(row) != replay::chunkHeader)
      throw std::runtime_error("replay manifest header");
    uint64_t indices[2]{};
    const char *names[] = {"events", "checkpoints"};
    const char *headers[] = {eventHeader, stateHeader};
    FILE *spools[] = {r.eventSpool.get(), r.stateSpool.get()};
    while (manifest.next(row, r.sourceIncomplete)) {
      if (row.size() != 5 || (row[0] != names[0] && row[0] != names[1]))
        throw std::runtime_error("replay manifest columns/stream");
      int stream = row[0] == names[0] ? 0 : 1;
      auto index = number(row[1]);
      if (index < 0 || uint64_t(index) != indices[stream] ||
          row[2] != replay::chunkName(names[stream], indices[stream]) ||
          row[4].size() != 64 || row[4].find_first_not_of("0123456789abcdef") != std::string::npos)
        throw std::runtime_error("replay manifest order/name/checksum");
      freezeChunk(directory / row[2], spools[stream], headers[stream], false,
                  row[4], positive(row[3]));
      ++indices[stream];
    }
    for (int stream = 0; stream < 2; ++stream) {
      path = directory / replay::chunkName(names[stream], indices[stream]);
      if (fs::exists(fs::symlink_status(path))) {
        if (!r.sourceIncomplete)
          throw std::runtime_error("unsealed chunk in complete replay");
        freezeChunk(path, spools[stream], headers[stream], true, "", 0,
                    stream == 0 ? &r.eventTruncated : nullptr);
      } else if (!indices[stream])
        throw std::runtime_error("missing initial replay chunk");
    }
    // Unknown numbered chunks can hide a deleted manifest entry or a gap.
    // Never silently recover around them.
    for (const auto &entry : fs::directory_iterator(directory)) {
      auto name = entry.path().filename().string();
      for (int stream = 0; stream < 2; ++stream) {
        std::string prefix = std::string(names[stream]) + ".";
        if (name == std::string(names[stream]) + ".csv" ||
            !name.starts_with(prefix) || !name.ends_with(".csv"))
          continue;
        auto digits = name.substr(prefix.size(), name.size() - prefix.size() - 4);
        auto index = number(digits);
        if (index < 1 || uint64_t(index) > indices[stream] ||
            name != replay::chunkName(names[stream], index))
          throw std::runtime_error("orphan or misnamed replay chunk");
      }
    }
  }
  rewindInput();
}
void validate() {
  size_t eventRow = 0;
  replay::Sha256 eventHash;
  eventHash.add(eventHeader);
  uint64_t seq = 1, cp = 0;
  std::vector<uint64_t> pumps;
  uint64_t pump = 0;
  const std::vector<std::string> kinds = {
      "clock", "localtime",  "pump_begin", "pump_end",   "input", "queued",
      "sleep", "cursor_set", "cursor_get", "checkpoint", "end"};
  Row row, state;
  bool haveState = r.stateReader->next(state);
  uint64_t stateId = 0;
  auto checkState = [&] {
    if (state.size() != 5)
      throw std::runtime_error("checkpoint columns");
    auto id = positive(state[0]);
    if (id < stateId || id > stateId + 1)
      throw std::runtime_error("checkpoint order");
    stateId = id;
    auto entity = number(state[2]);
    if (entity < INT32_MIN || entity > INT32_MAX)
      throw std::runtime_error("entity range");
    number(state[4]);
    return id;
  };
  while (r.eventReader->next(row)) {
    ++eventRow;
    if (r.complete) throw std::runtime_error("invalid completion marker");
    auto e = event(row);
    if (std::find(kinds.begin(), kinds.end(), e.kind) == kinds.end())
      throw std::runtime_error("unknown event kind");
    if (e.seq != seq || e.count > 65536 ||
        (e.kind != "clock" && e.count != 1) || seq > INT64_MAX - e.count)
      throw std::runtime_error("sequence/count discontinuity");
    seq += e.count;
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
      if (e.v[0] != int64_t(id) || e.v[1] < 1)
        throw std::runtime_error("missing checkpoint fields");
      replay::Sha256 stateHash;
      int64_t fields = 0;
      while (haveState && positive(state[0]) == id) {
        checkState();
        stateHash.add(csv(state));
        ++fields;
        haveState = r.stateReader->next(state);
      }
      if (fields != e.v[1])
        throw std::runtime_error("missing checkpoint fields");
      if (stateHash.finish() != e.detail)
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
  }
  while (haveState) {
    checkState();
    haveState = r.stateReader->next(state);
  }
  if (r.complete && r.eventTruncated)
    throw std::runtime_error("invalid completion marker");
  if (!eventRow)
    throw std::runtime_error("no recoverable events");
  rewindInput();
  r.prepared = true;
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
         !name.starts_with("E2R_LOG") && !name.starts_with("E2R_INSPECT") &&
         name != "E2R_AUDIO" && name != "E2R_AUDIO_TAP" && name != "E2R_AUDIO_TRACE" && name != "E2R_MUSIC_TRACE" && name != "E2R_MUSIC_TAP") ||
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
    validateMetadata();
    freeze(directory);
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
    if (!r.prepared &&
        (!gameplay || !record || std::string(record) == "off"))
      return 1;
    auto current = identity(game, argc, argv);
    r.sampler = sampler;
    r.stop = stopSeq;
    r.stopCheckpoint = stopCp;
    if (r.prepared) {
      r.mode = 2;
      r.compatible = compatible;
      for (const auto &[key, value] : r.metadata) {
        bool exactOnly = key == "executable_sha256" || key == "revision" ||
                         key == "asan" || key == "build";
        bool descriptive = key == "recording_id" || key == "wall_utc" ||
                           key == "game_data_path" || key == "storage" ||
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
      current["storage"] = "chunked.csv.1";
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
      uint64_t chunkLimit = 16u * 1024u * 1024u;
      if (const char *setting = std::getenv("E2R_REPLAY_CHUNK_BYTES")) {
        chunkLimit = positive(setting);
        if (chunkLimit < 512 || chunkLimit > 256u * 1024u * 1024u)
          throw std::runtime_error("E2R_REPLAY_CHUNK_BYTES must be 512..268435456");
      }
      r.manifest.reset(std::fopen((dir / "chunks.csv").c_str(), "wbx"));
      replay::put(r.manifest.get(), replay::chunkHeader);
      replay::sync(r.manifest.get());
      r.events.start(dir, "events", eventHeader, r.manifest.get(), chunkLimit);
      r.states.start(dir, "checkpoints", stateHeader, r.manifest.get(), chunkLimit);
      r.eventHash.add(eventHeader);
      flush(true);
      report("recording " + dir.string());
    }
    return 1;
  } catch (const std::exception &e) {
    if (r.prepared) {
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
    if ((r.seq & 65535) == 0 && r.hostControl)
      r.hostControl();
    const Event &e = pending();
    if (e.kind != "clock")
      return uint32_t(consume("clock").v[0]);
    if (r.stop && e.seq + r.expanded >= r.stop)
      stop(76, "stopped before requested clock call");
    r.seq = e.seq + r.expanded;
    E2R_replay_sequence = r.seq;
    uint32_t result = uint32_t(e.v[0]);
    advance(e);
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
  if (r.mode == 1) {
    for (auto *file : {&r.states, &r.events}) {
      try {
        file->finish(!r.failed);
      } catch (const std::exception &e) {
        fail(e.what());
      }
    }
    if (r.manifest && std::fclose(r.manifest.release()))
      fail("manifest close failed");
  }
  if (r.mode == 1 && !r.failed) {
    std::error_code error;
    fs::remove(r.incompleteMarker, error);
    if (error)
      fail("cannot publish clean completion");
  }
  r.mode = 0;
}
