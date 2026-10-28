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
bool volume = false;
const std::string volumeField(16000, 'x');
void sample() {
  E2R_ReplayField("actor", 0, "x", position);
  // A single checkpoint crosses multiple tiny test chunks, including quoting.
  for (int i = 0; i < 64; ++i)
    E2R_ReplayField("actor", i, volume ? volumeField.c_str() : "quoted,field\"\nvalue",
                    position + i);
}
void delivery(unsigned message, uintptr_t key, intptr_t lp) {
  assert((message == 256 || message == 257) && key == 38 && lp == 0);
  ++position;
}
int main(int argc, char **argv) {
  assert(argc >= 3);
  std::string mode = argv[1];
  fs::path root = argv[2];
  volume = mode.ends_with("volume");
  char *args[] = {const_cast<char *>("--run-recon")};
  const bool recording = mode.starts_with("record");
  if (recording) {
    fs::create_directories(root / "game/Files");
    std::ofstream(root / "game/E2WIN95.EXE") << "fixture";
    fs::create_directories(root / "session");
  } else if (!E2R_ReplayPrepare((root / "session/replay").c_str()))
    return 73;
  if (mode == "prepare")
    return 0;
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
  if (recording) {
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
  if (mode.ends_with("chunks")) {
    for (int i = 0; i < 96; ++i) {
      E2R_ReplayPumpBegin();
      if (i % 8 == 0)
        E2R_ReplayPumpBegin();
      if (recording) {
        unsigned message = i % 2 ? 256 : 257;
        E2R_ReplayInput(message, 38, 0, 0, 0);
        delivery(message, 38, 0);
      } else
        E2R_ReplayPumpInputs(delivery);
      if (i % 8 == 0)
        E2R_ReplayPumpEnd();
      E2R_ReplayPumpEnd();
    }
    assert(position == 99);
  }
  if (volume) {
    // Each logical stream independently exceeds the former 256 MiB ceiling.
    for (int i = 0; i < 300; ++i) {
      E2R_ReplayPumpBegin();
      if (recording) {
        unsigned message = i % 2 ? 256 : 257;
        E2R_ReplayInput(message, 38, 0, 0, 0);
        delivery(message, 38, 0);
      } else
        E2R_ReplayPumpInputs(delivery);
      E2R_ReplayPumpEnd();
    }
    for (int i = 0; i < 3700000; ++i)
      E2R_ReplayService("cursor_set", INT64_MAX, INT64_MAX);
  }
  std::fprintf(
      stderr, "contract: 2000001 clocks in %.3f seconds\n",
      std::chrono::duration<double>(std::chrono::steady_clock::now() - begin)
          .count());
  E2R_ReplayFinish();
  return 0;
}
