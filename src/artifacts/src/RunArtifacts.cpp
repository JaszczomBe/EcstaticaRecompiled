#include "RunArtifacts.h"
#include "Log/Session/SessionRetention.h"
#include <atomic>
#include <charconv>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <limits>
#include <stdexcept>
using namespace Ecstatica::Recompiled;
namespace {
std::unique_ptr<Log::Session::Maintenance> owner;
std::string directory;
std::atomic<void (*)(const char *)> report{nullptr};
uint64_t setting(const char *name, uint64_t fallback, uint64_t maximum) {
  const char *value = std::getenv(name);
  if (!value || !*value)
    return fallback;
  uint64_t parsed = 0;
  auto end = value + std::char_traits<char>::length(value);
  auto result = std::from_chars(value, end, parsed);
  if (result.ec != std::errc{} || result.ptr != end || !parsed ||
      parsed > maximum)
    throw std::invalid_argument(std::string(name) +
                                " must be a positive integer within range");
  return parsed;
}
struct SourceLock {
  std::unique_ptr<LogSupport::IO::FileLock> root, source;
};
} // namespace
extern "C" void E2R_ArtifactsSetReporter(void (*fn)(const char *)) {
  report.store(fn);
}
extern "C" void E2R_ArtifactsReport(const char *message) {
  if (auto fn = report.load())
    fn(message);
  else
    std::fprintf(stderr, "%s\n", message);
}
extern "C" int E2R_ArtifactsStart(const char *data) {
  if (owner)
    return 1;
  try {
    Log::Session::RetentionPolicy policy;
    policy.maxSessions = setting("E2R_LOG_MAX_SESSIONS", std::numeric_limits<unsigned>::max(),
                                 std::numeric_limits<unsigned>::max());
    policy.maxTotalSizeBytes =
        setting("E2R_LOG_MAX_TOTAL_MB", 2048, UINT64_MAX / (1024 * 1024)) *
        1024 * 1024;
    policy.cleanupInterval = std::chrono::seconds(
        setting("E2R_LOG_CLEANUP_INTERVAL_SECONDS", 60, INT32_MAX));
    Log::Session::Metadata meta{"EcstaticaRecompiled", "e2recomp.log",
                                5 * 1024 * 1024};
    auto root = (std::filesystem::path(data) / "logs").string();
    auto session =
        Log::Session::PrepareStartupSession(root, "e2recomp.log", policy, meta);
    if (session.sessionDirectory.empty() || !session.lease)
      return 0;
    directory = session.sessionDirectory;
    if (session.cleanup.removedSessions || session.cleanup.failedRemovals ||
        session.cleanup.overBudget)
      E2R_ArtifactsReport(
          Log::Session::FormatCleanupSummary(session.cleanup).c_str());
    owner = std::make_unique<Log::Session::Maintenance>(root, policy,
                                                        std::move(session));
    return 1;
  } catch (const std::exception &e) {
    std::fprintf(stderr, "artifact bootstrap failed: %s\n", e.what());
    return 0;
  }
}
extern "C" const char *E2R_ArtifactsDirectory(void) {
  return directory.c_str();
}
extern "C" void E2R_ArtifactsStopMaintenance(void) {
  if (owner)
    owner->Stop();
}
extern "C" void E2R_ArtifactsShutdown(void) {
  owner.reset();
  directory.clear();
  report.store(nullptr);
}
extern "C" void *E2R_ArtifactsLockSource(const char *path) {
  try {
    auto token = std::make_unique<SourceLock>();
    auto session = std::filesystem::canonical(path).parent_path();
    if (std::filesystem::exists(session / "session.meta") &&
        session.filename().string().starts_with("session_")) {
      token->root = LogSupport::IO::FileLock::TryAcquire(
          (session.parent_path() / ".retention.lock").string(), true);
      if (!token->root)
        return nullptr;
      token->source = LogSupport::IO::FileLock::TryAcquire(
          (session / "session.active.lock").string());
      if (!token->source)
        return nullptr;
    }
    return token.release();
  } catch (...) {
    return nullptr;
  }
}
extern "C" void E2R_ArtifactsUnlockSource(void *token) {
  delete static_cast<SourceLock *>(token);
}
