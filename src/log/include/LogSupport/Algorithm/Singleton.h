#pragma once

namespace Ecstatica::Recompiled::LogSupport::Algorithm
{


    template<class T>
    class Singleton
    {
    protected:
        Singleton(){};
    public:
        virtual ~Singleton() = default;

        Singleton(const Singleton&) = delete;
        Singleton(Singleton &&) = delete;

        Singleton& operator=(const Singleton &) = delete;
        Singleton& operator=(Singleton &&) = delete;

        static T& Instance()
        {
            static T instance;
            return instance;
        }
    };


}