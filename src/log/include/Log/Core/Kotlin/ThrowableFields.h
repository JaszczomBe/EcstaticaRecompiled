#pragma once

#include "Log/Core/Record.h"

#include <string_view>

namespace Ecstatica::Recompiled::Log
{
    struct KotlinThrowableFields
    {
        bool             present = false;
        std::string_view type;
        std::string_view message;
        std::string_view stack;
        std::string_view causeType;
        std::string_view causeMessage;
        std::string_view causeStack;
    };

    inline constexpr std::string_view kKotlinThrowablePresentKey = "kotlin_throwable_present";
    inline constexpr std::string_view kKotlinThrowableTypeKey = "kotlin_throwable_type";
    inline constexpr std::string_view kKotlinThrowableMessageKey = "kotlin_throwable_message";
    inline constexpr std::string_view kKotlinThrowableStackKey = "kotlin_throwable_stack";
    inline constexpr std::string_view kKotlinThrowableCauseTypeKey = "kotlin_throwable_cause_type";
    inline constexpr std::string_view kKotlinThrowableCauseMessageKey = "kotlin_throwable_cause_message";
    inline constexpr std::string_view kKotlinThrowableCauseStackKey = "kotlin_throwable_cause_stack";

    inline constexpr std::string_view KotlinThrowableFieldKey(FieldId id)
    {
        switch(id)
        {
            case FieldId::KotlinThrowablePresent: return kKotlinThrowablePresentKey;
            case FieldId::KotlinThrowableType: return kKotlinThrowableTypeKey;
            case FieldId::KotlinThrowableMessage: return kKotlinThrowableMessageKey;
            case FieldId::KotlinThrowableStack: return kKotlinThrowableStackKey;
            case FieldId::KotlinThrowableCauseType: return kKotlinThrowableCauseTypeKey;
            case FieldId::KotlinThrowableCauseMessage: return kKotlinThrowableCauseMessageKey;
            case FieldId::KotlinThrowableCauseStack: return kKotlinThrowableCauseStackKey;
            case FieldId::None: return {};
        }

        return {};
    }

    inline constexpr bool IsKotlinThrowableFieldId(FieldId id)
    {
        switch(id)
        {
            case FieldId::KotlinThrowablePresent:
            case FieldId::KotlinThrowableType:
            case FieldId::KotlinThrowableMessage:
            case FieldId::KotlinThrowableStack:
            case FieldId::KotlinThrowableCauseType:
            case FieldId::KotlinThrowableCauseMessage:
            case FieldId::KotlinThrowableCauseStack:
                return true;
            case FieldId::None:
                return false;
        }

        return false;
    }

    inline constexpr bool IsKotlinThrowableFieldKey(std::string_view key)
    {
        return key == kKotlinThrowablePresentKey || key == kKotlinThrowableTypeKey || key == kKotlinThrowableMessageKey ||
               key == kKotlinThrowableStackKey || key == kKotlinThrowableCauseTypeKey ||
               key == kKotlinThrowableCauseMessageKey || key == kKotlinThrowableCauseStackKey;
    }

    inline constexpr bool IsKotlinThrowableField(const Field& field)
    {
        return IsKotlinThrowableFieldId(field.id) || IsKotlinThrowableFieldKey(field.key);
    }

    inline constexpr Field MakeKotlinThrowableField(FieldId id, std::string_view value)
    {
        return Field{id, KotlinThrowableFieldKey(id), value};
    }

    inline KotlinThrowableFields ExtractKotlinThrowableFields(const Record& rec)
    {
        KotlinThrowableFields result;

        for(size_t i = 0; i < rec.fieldCount; ++i)
        {
            const auto& field = rec.fields[i];
            auto        id    = field.id;

            if(id == FieldId::None)
            {
                if(field.key == kKotlinThrowablePresentKey)
                    id = FieldId::KotlinThrowablePresent;
                else if(field.key == kKotlinThrowableTypeKey)
                    id = FieldId::KotlinThrowableType;
                else if(field.key == kKotlinThrowableMessageKey)
                    id = FieldId::KotlinThrowableMessage;
                else if(field.key == kKotlinThrowableStackKey)
                    id = FieldId::KotlinThrowableStack;
                else if(field.key == kKotlinThrowableCauseTypeKey)
                    id = FieldId::KotlinThrowableCauseType;
                else if(field.key == kKotlinThrowableCauseMessageKey)
                    id = FieldId::KotlinThrowableCauseMessage;
                else if(field.key == kKotlinThrowableCauseStackKey)
                    id = FieldId::KotlinThrowableCauseStack;
            }

            switch(id)
            {
                case FieldId::KotlinThrowablePresent:
                    result.present = field.value == "true";
                    break;
                case FieldId::KotlinThrowableType:
                    result.type = field.value;
                    break;
                case FieldId::KotlinThrowableMessage:
                    result.message = field.value;
                    break;
                case FieldId::KotlinThrowableStack:
                    result.stack = field.value;
                    break;
                case FieldId::KotlinThrowableCauseType:
                    result.causeType = field.value;
                    break;
                case FieldId::KotlinThrowableCauseMessage:
                    result.causeMessage = field.value;
                    break;
                case FieldId::KotlinThrowableCauseStack:
                    result.causeStack = field.value;
                    break;
                case FieldId::None:
                    break;
            }
        }

        return result;
    }
}
