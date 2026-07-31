#pragma once

#include "mpscq.h"
#include <cstddef>
#include <cstdint>
#include <memory>

namespace Ecstatica::Recompiled::LogSupport::Algorithm
{

	///////////////////////////////////////////////////////////////////////////
    // Multiple provider signle consumer queue

    template<class T>
    class MPSCQueue
    {
    public:
		MPSCQueue() = default;
		~MPSCQueue();

        MPSCQueue(const MPSCQueue&) = delete;
        MPSCQueue& operator=(const MPSCQueue&) = delete;

        bool                        Initialize(size_t capacity);
        bool                        IsInitialized() const { return queue != nullptr; }
        size_t                      Count() const { return queue ? mpscq_count(queue) : 0; }
        size_t                      Capacity() const { return queue ? mpscq_capacity(queue) : 0; }

        // RT-safe API: caller owns object lifetime and must avoid allocations on RT path.
        bool                        TryEnqueueRaw(T* itemPtr);
        T*                          TryDequeueRaw();

        // Convenience API for non-RT paths.
        bool                        Enqueue(std::unique_ptr<T> itemUPtr);
        std::unique_ptr<T>          Dequeue();


    private:
        static size_t               RoundUpPowerOfTwo(size_t value);
        mpscq* queue = nullptr;
    };

	///////////////////////////////////////////////////////////////////////////


	template<class T>
	size_t MPSCQueue<T>::RoundUpPowerOfTwo(size_t value)
	{
		if (value < 2)
            return 2;

        --value;
        for (size_t shift = 1; shift < (sizeof(size_t) * 8); shift <<= 1)
            value |= (value >> shift);
        return value + 1;
	}

	template<class T>
	bool MPSCQueue<T>::Initialize(size_t capacity)
	{
        if (queue)
            mpscq_destroy(queue);

        const size_t roundedCapacity = RoundUpPowerOfTwo(capacity);
		queue = mpscq_create(nullptr, roundedCapacity);
        return queue != nullptr;
	}

    template<class T>
    bool MPSCQueue<T>::TryEnqueueRaw(T* itemPtr)
    {
        if (!queue || itemPtr == nullptr)
            return false;

        return mpscq_enqueue(queue, static_cast<void*>(itemPtr));
    }

    template<class T>
    T* MPSCQueue<T>::TryDequeueRaw()
    {
        if (!queue)
            return nullptr;

        return static_cast<T*>(mpscq_dequeue(queue));
    }

	template<class T>
	MPSCQueue<T>::~MPSCQueue()
	{
		if(queue)
			mpscq_destroy(queue);
	}

	template<class T>
	bool MPSCQueue<T>::Enqueue(std::unique_ptr<T> itemUPtr)
	{
        if (!itemUPtr)
            return false;

		auto item = itemUPtr.release();
		if(!TryEnqueueRaw(item))
		{
			delete item;
			return false;
		}

		return true;
	}

	template<class T>
	std::unique_ptr<T> MPSCQueue<T>::Dequeue()
	{
        T* item = TryDequeueRaw();
        if(item == nullptr)
            return nullptr;

		return std::unique_ptr<T>(item);
	}



	///////////////////////////////////////////////////////////////////////////	

}
