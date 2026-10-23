#include "EcstaticaInspect.h"
#include "EcstaticaReplay.h"
#include <charconv>
#include <cstdio>
#include <cstdlib>
#include <deque>
#include <filesystem>
#include <map>
#include <string>
#include <vector>

namespace {
namespace fs = std::filesystem;
FILE *timeline, *states;
E2R_InspectSampler sample;
uint64_t ordinal, update, present, snapshot, frame, bytes;
unsigned interval = 30, frameInterval = 30, maxFrames = 20;
bool collecting, failed, frameRequested;
bool framesAvailable = true;
std::deque<uint64_t> retainedFrames;
fs::path directory;
std::string prefix;
using Key = std::pair<std::string, int>;
std::map<Key, std::map<std::string, int64_t>> previous, current;
constexpr uint64_t maxBytes = 32u * 1024u * 1024u;
unsigned setting(const char *name, unsigned fallback, unsigned maximum) {
  auto s = std::getenv(name);
  if (!s || !*s) return fallback;
  unsigned value = 0;
  auto parsed = std::from_chars(s, s + std::char_traits<char>::length(s), value);
  if (parsed.ec != std::errc{} || *parsed.ptr || !value || value > maximum)
    throw std::runtime_error(std::string("invalid ") + name);
  return value;
}
void disable(const char *reason) {
  if (!failed) std::fprintf(stderr, "inspection incomplete: %s\n", reason);
  failed = true;
}
bool write(FILE *file, const std::string &row) {
  if (failed) return false;
  if (row.size() > maxBytes - bytes) { disable("32 MiB state/timeline limit reached"); return false; }
  bytes += row.size();
  if (!file || std::fwrite(row.data(), 1, row.size(), file) != row.size() || std::fflush(file)) {
    disable("write/flush failed; gameplay continues"); return false;
  }
  return true;
}
void event(const char *kind, int64_t a, int64_t b, uint64_t id) {
  write(timeline, std::to_string(++ordinal) + "," + std::to_string(E2R_replay_sequence) + "," +
    std::to_string(E2R_replay_last_checkpoint) + "," + std::to_string(update) + "," +
    std::to_string(present) + "," + std::to_string(id) + "," + kind + "," +
    std::to_string(a) + "," + std::to_string(b) + "\n");
}
}
extern "C" void E2R_InspectStart(const char *session, E2R_InspectSampler sampler) {
  auto enabled = std::getenv("E2R_INSPECT");
  if (!enabled || std::string(enabled) != "1") return;
  try {
    interval = setting("E2R_INSPECT_INTERVAL", 30, 1000000);
    frameInterval = setting("E2R_INSPECT_FRAME_INTERVAL", 30, 1000000);
    maxFrames = setting("E2R_INSPECT_MAX_FRAMES", 20, 100);
    directory = fs::path(session) / "inspection";
    if (!fs::create_directory(directory)) throw std::runtime_error("inspection destination exists");
    auto marker = std::fopen((directory / "inspection.incomplete").c_str(), "wx");
    if (!marker) throw std::runtime_error("cannot publish incomplete marker");
    std::fputs("Active, interrupted or failed observational capture.\n", marker);
    if (std::fclose(marker)) throw std::runtime_error("cannot close incomplete marker");
    timeline = std::fopen((directory / "timeline.csv").c_str(), "wx");
    states = std::fopen((directory / "state.csv").c_str(), "wx");
    sample = sampler;
    write(timeline, "event_id,replay_sequence,replay_checkpoint,update_id,present_id,snapshot_id,kind,a,b\n");
    write(states, "snapshot_id,scope,entity_id,field,value,present\n");
    std::fprintf(stderr, "inspection: %s\n", directory.c_str());
    E2R_InspectObserve("start", 0, 0);
  } catch (const std::exception &e) { disable(e.what()); }
}
extern "C" void E2R_InspectField(const char *scope, int id, const char *name, int64_t value) {
  if (collecting) current[{scope, id}][name] = value;
}
extern "C" void E2R_InspectObserve(const char *kind, int64_t a, int64_t b) {
  if (!timeline || failed || collecting) return;
  try {
  current.clear(); collecting = true;
  if (sample) sample();
  collecting = false;
  for (const auto &key : {Key{"world", 0}, Key{"actor", 0}}) {
    const char *name = key.first == "world" ? "camera" : "action_id";
    auto before = previous.find(key), after = current.find(key);
    if (after != current.end() && after->second.count(name) &&
        (before == previous.end() || !before->second.count(name) ||
         before->second.at(name) != after->second.at(name))) frameRequested = true;
  }
  if (std::string(kind) == "bookmark") frameRequested = true;
  ++snapshot;
  std::string rows;
  for (const auto &[key, fields] : current)
    for (const auto &[name, value] : fields) {
      auto entity = previous.find(key);
      if (entity == previous.end() || !entity->second.count(name) || entity->second.at(name) != value)
        rows += std::to_string(snapshot) + "," + key.first + "," + std::to_string(key.second) + "," +
          name + "," + std::to_string(value) + ",1\n";
    }
  for (const auto &[key, fields] : previous)
    for (const auto &[name, value] : fields) {
      (void)value;
      auto entity = current.find(key);
      if (entity == current.end() || !entity->second.count(name))
        rows += std::to_string(snapshot) + "," + key.first + "," + std::to_string(key.second) + "," + name + ",0,0\n";
    }
  // State changes are published before their timeline reference. No engine writes,
  // projection helpers, or game-visible clock reads are performed by this observer.
  if (write(states, rows)) event(kind, a, b, snapshot);
  previous = std::move(current);
  } catch (const std::exception &e) { collecting = false; disable(e.what()); }
}
extern "C" void E2R_InspectUpdate(int completed) {
  if (!timeline || failed) return;
  if (!completed) ++update;
  if (update == 1 || update % interval == 0)
    E2R_InspectObserve(completed ? "update_end" : "update_begin", 0, 0);
}
extern "C" const char *E2R_InspectPresent(void) {
  if (!timeline || failed) return nullptr;
  ++present;
  if (!framesAvailable) return nullptr;
  if (present != 1 && present % frameInterval && !frameRequested) return nullptr;
  frameRequested = false;
  ++frame;
  try { prefix = (directory / ("frame-" + std::to_string(frame))).string(); }
  catch (const std::exception &e) { disable(e.what()); return nullptr; }
  E2R_InspectObserve("frame", frame, 0);
  return failed ? nullptr : prefix.c_str();
}
extern "C" void E2R_InspectFrameResult(int success) {
  if (!timeline || failed) return;
  try {
    if (success < 0) {
      framesAvailable = false;
      event("frame_unavailable", 0, 0, snapshot);
      return;
    }
    event(success ? "frame_written" : "frame_failed", frame, 0, snapshot);
    if (!success) { disable("frame write failed"); return; }
    retainedFrames.push_back(frame);
    if (retainedFrames.size() > maxFrames) {
      auto old = retainedFrames.front();
      std::error_code error;
      fs::remove(directory / ("frame-" + std::to_string(old) + ".ppm"), error);
      if (error) { disable("cannot remove old frame"); return; }
      retainedFrames.pop_front();
      event("frame_evicted", old, 0, snapshot);
    }
  } catch (const std::exception &e) { disable(e.what()); }
}
extern "C" void E2R_InspectFinish(void) {
  if (!timeline && !states) return;
  if (!failed) E2R_InspectObserve("end", 0, 0);
  for (auto f : {states, timeline}) if (f && std::fclose(f)) disable("close failed");
  states = timeline = nullptr;
  if (!failed) {
    std::error_code error;
    fs::remove(directory / "inspection.incomplete", error);
    if (error) disable("cannot publish completion");
  }
}
