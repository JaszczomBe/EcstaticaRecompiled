#pragma once

#include <cstdint>
#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    enum class FieldId : std::uint8_t
    {
        None = 0,
        KotlinThrowablePresent,
        KotlinThrowableType,
        KotlinThrowableMessage,
        KotlinThrowableStack,
        KotlinThrowableCauseType,
        KotlinThrowableCauseMessage,
        KotlinThrowableCauseStack
    };

    struct Field
    {
        constexpr Field() = default;

        constexpr Field(std::string_view keyIn, std::string_view valueIn)
            : id(FieldId::None), key(keyIn), value(valueIn)
        {
        }

        constexpr Field(FieldId idIn, std::string_view keyIn, std::string_view valueIn)
            : id(idIn), key(keyIn), value(valueIn)
        {
        }

        FieldId          id = FieldId::None;
        std::string_view key;
        std::string_view value;
    };
}
