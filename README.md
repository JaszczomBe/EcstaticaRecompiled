# Ecstatica Recompiled

This checkout develops an experimental reconstruction of **Ecstatica II on Linux/i386**, using original game data. It loads resources, runs bounded engine probes, accepts arrow-key input, and presents recovered 640x480 frames through SDL. Visible actor rendering and playable behavior are still under recovery.

The completed reconstruction milestone is a historical state/surface proof. It is not a completed 64-bit Windows port, a D3D12/1080p renderer, or a verified 60-FPS release. Ecstatica I is part of the original project name; the active implementation here concerns Ecstatica II.

## Start Here

- [Handoff and workflow](docs/HANDOFF.md)
- [Current runtime status and next tasks](docs/implementations/playable-sdl-runtime/playable-sdl-runtime.md)
- [Build and launch instructions](E2Recomp/reconstructed/README.md)
- [Decompilation and generation workflow](E2Recomp/README.md)
- [2026-09-14 audit and reproducible checks](docs/journal/entries/runtime-audit-2026-09-14.md)

## SDL Launch

With a 32-bit Clang toolchain, CMake, Ninja, the SDL submodule, and your original game data available, run from the repository root:

```sh
git submodule update --init --recursive dep/SDL
cmake --preset linux-clang32-sdl-debug -DECSTATICA2_DATA_DIR=/path/to/Ecstatica2
cmake --build --preset linux-clang32-sdl-debug
./build/linux-clang32-sdl-debug/e2recomp --run-recon
```

The SDL VS Code launch entry is `Ecstatica Recompiled (SDL)`. X11 remains the default backend. Runtime execution requires the 32-bit build; the 64-bit target is a scaffold. Audio is stubbed, quick-save is a no-op, and functional save/load is unproven. Original game data is required separately.

## Original Project Credit

Original project presentation: Spacefarer Retro Remasters. Existing support links: [Buy Me a Coffee](https://buymeacoffee.com/jakeysbakery), PayPal `jake@spacefarergames.com`. See [LICENSE](LICENSE).

## Original-Game Control Reference

The reference tables below describe the original game, not a list of implemented reconstructed behavior. The current automated matrix proves the four arrow-key latches; most action/status behavior remains unclassified. F12 currently also requests a developer visibility packet, so its original healing behavior is not verified. Follow the active implementation for accepted controls.

Basic Keyboard Layout

Below is a table displaying all keyboard commands including descriptions of the actions. Note that the game does not provide an internal option to remap the controls but an external tool like DOSBox' Mapper program can be used to rebind the keys for inreased convenience (it also allows mapping to gamepads).
Command 	Key 	Description
Move forward 	↑ 	A tap will make the character execute a single careful step.
Move backwards 	↓ 	
Turn left 	← 	
Turn right 	→ 	
Basic attacks 	Ctrl + Cursor keys 	When the control key is held down the cursor keys will execute different kinds of attacks instead of moving the character.
Advanced attacks 	Ctrl + Left Alt + Cursor keys 	When the control and alt keys are held down the cursor keys will execute different kinds of attacks instead of moving the character.
Dodge roll 	Left Alt + Cursor keys 	Executes a dodge roll in the direction specified by the cursor keys.
Jump 	Left Shift 	Executes a small jump suitable for skipping some traps and short gaps. Can only be executed forwards.
Use, pick up / drop item or weapon 	Space 	Makes the hero interact with environmental objects or pick up / drop items. Weapons cannot be dropped, only replaced.
Drop weapon or item 	Right Alt 	Makes the hero drop whatever he is carrying in his hands.
Open Icon Page 	Return 	Displays a statistics and inventory screen.
Instant healing 	F12 	Instantly fully regenerates the hero at a cost of 30,000 gold pieces.
Menu 	Escape 	Allows to save / load the game, access options and quit the game.
Quick save 	S 	Saves the game in a special quick save slot.
Hide / display Icon Bar 	I 	Hides or reveals the HUD.
Detailed Keyboard Layout

The exact actions executed by the character are largely dependent on the weapon/magic currently wielded and some other factors. The tables listed below describe each individual scenario in detail. The content of these tables is based entirely on the original game manual.
Unarmed

This is the command layout when the hero neither wields weapons nor magic.
Cursor keys 	↑ 	↓ 	← 	→
	Run forwards 	Walk backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Double punch 	180° Elbow / Fist swipe 	Front left punch 	Front chop kick
Cursor key + Left alt 	Front flip 	Back flip 	Left roll 	Right roll
Cursor key + Ctrl + Left alt 	Front right punch 	Round house kick 	Left upper cut 	Right upper cut
Armed

This is the command layout when the hero is armed but not able to cast magic.
Cursor keys 	↑ 	↓ 	← 	→
	Run forwards 	Walk backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Front stab 	180° back swipe 	Swipe 	Front chop kick
Cursor key + Left alt 	Front flip 	Back flip 	Left roll 	Right roll
Cursor key + Ctrl + Left alt 	Forward left punch 	360° swipe 	High head kick 	Round house kick
Wielding Magic

This is the command layout when the hero is unarmed but able to cast magic.
Cursor keys 	↑ 	↓ 	← 	→
	Run forwards 	Walk backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Double punch 	180° Elbow / Fist swipe 	Front left punch 	Front chop kick
Cursor key + Left alt 	Front flip 	Back flip 	Left roll 	Right roll
Cursor key + Ctrl + Left alt 	Double handed magic

Lightning (medium power)
	Smart bomb

(strong power)
	Left handed magic

fire bombs (weak power)
	Right upper cut
Wielding Arms and Magic

This is the command layout when the hero is both armed and able to cast magic.
Cursor keys 	↑ 	↓ 	← 	→
	Run forwards 	Walk backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Front stab 	180° back swipe 	Swipe 	Front chop kick
Cursor key + Left alt 	Front flip 	Back flip 	Left roll 	Right roll
Cursor key + Ctrl + Left alt 	360° swipe 	Smart bomb

(strong power)
	Left handed magic

fire bombs (weak power)
	Round house kick
Swimming Unarmed

This is the command layout when the hero is unarmed in deep water. Note that the hero is not able to pick up or drop items while swimming.
Cursor keys 	↑ 	↓ 	← 	→
	Swim forwards 	Swim backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Swim punch left 	180° Elbow / Fist back swipe 	Left swim punch 	Right swim punch
Cursor key + Left alt 	Swim punch left 	180° Elbow / Fist back swipe 	Left swim punch 	Right swim punch
Cursor key + Ctrl + Left alt 	Swim punch left 	180° Elbow / Fist back swipe 	Left swim punch 	Right swim punch
Swimming Armed

This is the command layout when the hero is in deep water and wielding a weapon. Note that the hero is not able to pick up or drop items while swimming.
Cursor keys 	↑ 	↓ 	← 	→
	Swim forwards 	Swim backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Front swipe 	180° back swipe 	Front swipe 	Front swipe
Cursor key + Left alt 	Front swipe 	180° back swipe 	Front swipe 	Front swipe
Cursor key + Ctrl + Left alt 	Front swipe 	180° back swipe 	Front swipe 	Front swipe
Armed with a magic weapon

This is the command layout when the hero is armed with a magic weapon but is not able to cast magic himself.
Cursor keys 	↑ 	↓ 	← 	→
	Run forwards 	Walk backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Wand magic 	180° back swipe 	Swipe 	Front chop kick
Cursor key + Left alt 	Front flip 	Back flip 	Left roll 	Right roll
Cursor key + Ctrl + Left alt 	Forward left punch 	360° swipe 	High head kick 	Round house kick
Armed with a magic weapon and wielding magic

This is the command layout when the hero is armed with a magic weapon and able to cast magic himself.
Cursor keys 	↑ 	↓ 	← 	→
	Run forwards 	Walk backwards 	Turn left 	Turn right
Cursor key + Ctrl 	Wand magic 	180° back swipe 	Swipe 	Front chop kick
Cursor key + Left alt 	Front flip 	Back flip 	Left roll 	Right roll
Cursor key + Ctrl + Left alt 	Smart bomb

(strong power)
	360° swipe 	Left handed magic

fire bombs (weak power)
	Round house kick 

<img width="1536" height="1024" alt="EC2Recomp" src="https://github.com/user-attachments/assets/075a3032-6f1f-4af8-a826-4bc009e2a5f9" />

<img width="640" height="480" alt="image" src="https://github.com/user-attachments/assets/4ece3d14-54d9-47f7-b96f-46216bd12594" />
