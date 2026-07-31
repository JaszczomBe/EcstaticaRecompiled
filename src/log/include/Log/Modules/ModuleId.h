#pragma once

#include <array>
#include <bit>
#include <cstdint>
#include <optional>
#include <string_view>
#include <vector>

namespace Ecstatica::Recompiled::Log
{
    enum class ModuleID : std::uint64_t
    {
        None = 0,

        Runtime           = 1ull << 0,
        Win32Compat       = 1ull << 1,
        HostBackend       = 1ull << 2,
        DirectDrawCompat  = 1ull << 3,
        DirectSoundCompat = 1ull << 4,
        Probe             = 1ull << 5,
        Reconstruction    = 1ull << 6,
        Script            = 1ull << 7,
        Actor             = 1ull << 8,
        Requester         = 1ull << 9,
        FileIO            = 1ull << 10,
        Presentation      = 1ull << 11,
        Timing            = 1ull << 12,
        Audio             = 1ull << 13,

        // Reserved slots. Add new static module ids here as needed.
        Reserved_14 = 1ull << 14,
        Reserved_15 = 1ull << 15,
        Reserved_16 = 1ull << 16,
        Reserved_17 = 1ull << 17,
        Reserved_18 = 1ull << 18,
        Reserved_19 = 1ull << 19,
        Reserved_20 = 1ull << 20,
        Reserved_21 = 1ull << 21,
        Reserved_22 = 1ull << 22,
        Reserved_23 = 1ull << 23,
        Reserved_24 = 1ull << 24,
        Reserved_25 = 1ull << 25,
        Reserved_26 = 1ull << 26,
        Reserved_27 = 1ull << 27,
        Reserved_28 = 1ull << 28,
        Reserved_29 = 1ull << 29,
        Reserved_30 = 1ull << 30,
        Reserved_31 = 1ull << 31,
        Reserved_32 = 1ull << 32,
        Reserved_33 = 1ull << 33,
        Reserved_34 = 1ull << 34,
        Reserved_35 = 1ull << 35,
        Reserved_36 = 1ull << 36,
        Reserved_37 = 1ull << 37,
        Reserved_38 = 1ull << 38,
        Reserved_39 = 1ull << 39,
        Reserved_40 = 1ull << 40,
        Reserved_41 = 1ull << 41,
        Reserved_42 = 1ull << 42,
        Reserved_43 = 1ull << 43,
        Reserved_44 = 1ull << 44,
        Reserved_45 = 1ull << 45,
        Reserved_46 = 1ull << 46,
        Reserved_47 = 1ull << 47,
        Reserved_48 = 1ull << 48,
        Reserved_49 = 1ull << 49,
        Reserved_50 = 1ull << 50,
        Reserved_51 = 1ull << 51,
        Reserved_52 = 1ull << 52,
        Reserved_53 = 1ull << 53,
        Reserved_54 = 1ull << 54,
        Reserved_55 = 1ull << 55,
        Reserved_56 = 1ull << 56,
        Reserved_57 = 1ull << 57,
        Reserved_58 = 1ull << 58,
        Reserved_59 = 1ull << 59,
        Reserved_60 = 1ull << 60,
        Reserved_61 = 1ull << 61,
        Reserved_62 = 1ull << 62,
        Reserved_63 = 1ull << 63,
    };

    using ModuleMask = std::uint64_t;
    using SubmoduleMask = std::uint64_t;

    constexpr ModuleMask ToMask(ModuleID id) noexcept { return static_cast<ModuleMask>(id); }
    constexpr ModuleMask operator|(ModuleID lhs, ModuleID rhs) noexcept { return ToMask(lhs) | ToMask(rhs); }
    constexpr ModuleMask operator|(ModuleMask lhs, ModuleID rhs) noexcept { return lhs | ToMask(rhs); }
    constexpr ModuleMask& operator|=(ModuleMask& lhs, ModuleID rhs) noexcept { lhs |= ToMask(rhs); return lhs; }
    constexpr bool HasModule(ModuleMask mask, ModuleID id) noexcept { return (mask & ToMask(id)) != 0; }
    constexpr SubmoduleMask MakeSubmoduleMask(unsigned bit) { return bit < 64 ? (1ull << bit) : 0ull; }
    constexpr bool HasSubmodule(SubmoduleMask mask, unsigned bit) { return bit < 64 ? (mask & (1ull << bit)) != 0 : false; }

    std::string_view ModuleToString(ModuleID id) noexcept;
    std::vector<std::string_view> ModuleMaskToStrings(ModuleMask mask);
    std::optional<ModuleID> SingleModuleFromMask(ModuleMask mask) noexcept;

    // Reverse lookup for canonical static module names.
    std::optional<ModuleID> ModuleFromString(std::string_view name) noexcept;
}
