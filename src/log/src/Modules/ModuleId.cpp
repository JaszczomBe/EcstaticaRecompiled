#include "Log/Modules/ModuleId.h"
#include "LogSupport/String/Trim.h"

#include <algorithm>
#include <bit>

namespace Ecstatica::Recompiled::Log
{
    namespace
    {
        constexpr std::array<std::string_view, 65> MODULE_NAMES = {
            "None",
            "Runtime",           "Win32Compat",       "HostBackend",       "DirectDrawCompat",
            "DirectSoundCompat",  "Probe",             "Reconstruction",    "Script",
            "Actor",             "Requester",         "FileIO",            "Presentation",
            "Timing",            "Audio",
            "reserved_14",       "reserved_15",       "reserved_16",       "reserved_17",
            "reserved_18",       "reserved_19",       "reserved_20",       "reserved_21",
            "reserved_22",       "reserved_23",       "reserved_24",       "reserved_25",
            "reserved_26",
            "reserved_27",       "reserved_28",       "reserved_29",       "reserved_30",
            "reserved_31",
            "reserved_32",       "reserved_33",       "reserved_34",       "reserved_35",
            "reserved_36",       "reserved_37",       "reserved_38",       "reserved_39",
            "reserved_40",       "reserved_41",       "reserved_42",       "reserved_43",
            "reserved_44",       "reserved_45",       "reserved_46",       "reserved_47",
            "reserved_48",       "reserved_49",       "reserved_50",       "reserved_51",
            "reserved_52",       "reserved_53",       "reserved_54",       "reserved_55",
            "reserved_56",       "reserved_57",       "reserved_58",       "reserved_59",
            "reserved_60",       "reserved_61",       "reserved_62",       "reserved_63"
        };

        constexpr std::size_t kModuleNameCount = MODULE_NAMES.size();

        template<typename EnumT>
        std::optional<EnumT> FromString(std::string_view name,
                                        const std::array<std::string_view, 65>& lookup) noexcept
        {
            if (name.empty())
                return EnumT::None;

            auto it = std::find(lookup.begin(), lookup.end(), name);
            if (it == lookup.end())
                return std::nullopt;

            const std::size_t index = static_cast<std::size_t>(std::distance(lookup.begin(), it));
            if (index == 0)
                return EnumT::None;

            return static_cast<EnumT>(1ull << (index - 1));
        }

    } // namespace

    std::string_view ModuleToString(ModuleID id) noexcept
    {
        const auto value = static_cast<std::uint64_t>(id);
        if(value == 0)
            return MODULE_NAMES.front();

        if((value & (value - 1)) != 0)
            return "Composite";

        const std::size_t index = static_cast<std::size_t>(std::countr_zero(value)) + 1;
        if(index >= kModuleNameCount)
            return "Unknown";

        return MODULE_NAMES[index];
    }

    std::vector<std::string_view> ModuleMaskToStrings(ModuleMask mask)
    {
        std::vector<std::string_view> result;
        if(mask == 0)
        {
            result.emplace_back(MODULE_NAMES.front());
            return result;
        }
        uint64_t remaining = mask;
        while(remaining != 0)
        {
            const auto bit = std::countr_zero(remaining);
            const std::size_t nameIndex = static_cast<std::size_t>(bit) + 1;
            if(nameIndex < kModuleNameCount)
                result.emplace_back(MODULE_NAMES[nameIndex]);
            remaining &= ~(1ull << bit);
        }
        return result;
    }

    std::optional<ModuleID> SingleModuleFromMask(ModuleMask mask) noexcept
    {
        if (mask == 0 || (mask & (mask - 1)) != 0)
            return std::nullopt;

        const auto bit = std::countr_zero(mask);
        if (bit >= 64)
            return std::nullopt;

        return static_cast<ModuleID>(1ull << bit);
    }

    std::optional<ModuleID> ModuleFromString(std::string_view name) noexcept
    {
        name = Ecstatica::Recompiled::LogSupport::String::TrimAsciiWhitespace(name);
        return FromString<ModuleID>(name, MODULE_NAMES);
    }

}
