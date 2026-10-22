#include "EcstaticaReplay.h"
#include <cassert>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
namespace fs = std::filesystem;
int position = 0;
void sample() { E2R_ReplayField("actor", 0, "x", position); }
void delivery(unsigned message, uintptr_t key, intptr_t lp) {
  assert(message == 256 && key == 38 && lp == 0);
  ++position;
}
int main(int argc, char **argv) {
  assert(argc >= 3);
  std::string mode = argv[1];
  fs::path root = argv[2];
  char *args[] = {const_cast<char *>("--run-recon")};
  const bool recording = mode == "record" || mode == "record-clock-crash";
  if (recording) {
    fs::create_directories(root / "game/Files");
    std::ofstream(root / "game/E2WIN95.EXE") << "fixture";
    fs::create_directories(root / "session");
  } else if (!E2R_ReplayPrepare((root / "session/replay").c_str()))
    return 73;
  if (!E2R_ReplayStart("auto", 1, (root / "session").c_str(),
                       (root / "game").c_str(), 1, args, 0, 0, 0, sample))
    return 73;
  if (mode == "diverge")
    position = 99;
  auto begin = std::chrono::steady_clock::now();
  // Must preserve counts across a run-length split and >65536 unchanged polls.
  for (int i = 0; i < 2000000; ++i)
    assert(E2R_ReplayClock(123) == 123);
  assert(E2R_ReplayClock(124) == 124);
  if (mode == "record-clock-crash" || mode == "play-clock-crash") {
    assert(E2R_replay_sequence == 2000001);
    std::fprintf(stderr, "contract: reached crash-triggering changed clock\n");
    std::_Exit(42); // No Finish, fclose or shutdown handlers.
  }
  E2R_ReplayPumpBegin();
  if (mode == "record") {
    for (int i = 0; i < 3; ++i) {
      E2R_ReplayInput(256, 38, 0, 0, 0);
      delivery(256, 38, 0);
    }
  } else
    E2R_ReplayPumpInputs(delivery);
  E2R_ReplayPumpEnd();
  assert(position == 3);
  uint16_t local[8] = {2026, 10, 4, 22, 17, 0, 0, 0};
  E2R_ReplayLocalTime(local);
  E2R_ReplayService("cursor_set", 12, 34);
  E2R_ReplayService("cursor_get", 12, 34);
  E2R_ReplayService("sleep", 0, 0);
  E2R_ReplayPumpBegin();
  E2R_ReplayPumpInputs(delivery);
  E2R_ReplayPumpEnd();
  std::fprintf(
      stderr, "contract: 2000001 clocks in %.3f seconds\n",
      std::chrono::duration<double>(std::chrono::steady_clock::now() - begin)
          .count());
  E2R_ReplayFinish();
  return 0;
}
