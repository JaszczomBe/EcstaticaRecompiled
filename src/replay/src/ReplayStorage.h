#pragma once
#include "Sha256.h"
#include <array>
#include <cstdio>
#include <filesystem>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>
#include <unistd.h>

namespace replay {
using File = std::unique_ptr<FILE, decltype(&std::fclose)>;
inline File temporary() {
  File file(std::tmpfile(), std::fclose);
  if (!file)
    throw std::runtime_error("cannot create immutable replay spool");
  return file;
}
inline void put(FILE *file, const std::string &bytes) {
  if (!file || std::fwrite(bytes.data(), 1, bytes.size(), file) != bytes.size())
    throw std::runtime_error("replay write failed (gameplay continues)");
}
inline void sync(FILE *file) {
  if (std::fflush(file) || ::fsync(::fileno(file)))
    throw std::runtime_error("replay flush/sync failed");
}

// One bounded CSV record in memory, including quoted embedded newlines. The
// block buffer also hashes the exact source bytes for sealed-chunk integrity.
class CsvReader {
  FILE *file;
  std::array<char, 65536> buffer{};
  size_t offset = 0, available = 0;
  Sha256 hash;
  int peek() {
    if (offset == available) {
      available = std::fread(buffer.data(), 1, buffer.size(), file);
      offset = 0;
      if (std::ferror(file))
        throw std::runtime_error("replay read failed");
      hash.add(std::string_view(buffer.data(), available));
      if (!available)
        return EOF;
    }
    return static_cast<unsigned char>(buffer[offset]);
  }
  int get() {
    int c = peek();
    if (c != EOF)
      ++offset;
    return c;
  }
public:
  bool truncated = false;
  explicit CsvReader(FILE *source) : file(source) {}
  std::string checksum() const {
    auto copy = hash;
    return copy.finish();
  }
  bool next(std::vector<std::string> &row, bool recover = false) {
    row.clear();
    std::string field;
    bool quoted = false, closed = false, start = true;
    size_t length = 0;
    for (int c; (c = get()) != EOF;) {
      if (!c || ++length > 65536)
        throw std::runtime_error("CSV record exceeds limit or contains NUL");
      if (quoted) {
        if (c == '"') {
          if (peek() == '"') {
            get();
            ++length;
            field += '"';
          } else {
            quoted = false;
            closed = true;
          }
        } else
          field += char(c);
        continue;
      }
      if (c == '"' && start) {
        quoted = true;
        start = false;
        continue;
      }
      if (c == ',' || c == '\n' || (c == '\r' && peek() == '\n')) {
        row.push_back(std::move(field));
        field.clear();
        start = true;
        closed = false;
        if (c != ',') {
          if (c == '\r')
            get();
          return true;
        }
        continue;
      }
      if (closed || c == '"' || c == '\r')
        throw std::runtime_error("invalid CSV quoting");
      field += char(c);
      start = false;
    }
    if (length) {
      if (!recover)
        throw std::runtime_error("truncated CSV record");
      truncated = true;
    }
    return false;
  }
};

inline std::string chunkName(const std::string &stream, uint64_t index) {
  if (!index)
    return stream + ".csv";
  auto digits = std::to_string(index);
  return stream + "." + std::string(digits.size() < 6 ? 6 - digits.size() : 0, '0') +
         digits + ".csv";
}
constexpr const char *chunkHeader = "stream,index,file,bytes,sha256\n";

// Seal the old chunk durably before publishing its manifest row. A crash can
// leave at most one unsealed tail per stream. Headers repeat in physical files;
// logical event/checkpoint hashes still cover only one header.
class ChunkWriter {
  File file{nullptr, std::fclose};
  FILE *manifest = nullptr;
  std::filesystem::path directory;
  std::string stream, header;
  uint64_t index = 0, bytes = 0, limit = 0;
  Sha256 hash;
  void open() {
    auto path = directory / chunkName(stream, index);
    file.reset(std::fopen(path.c_str(), "wbx"));
    if (!file)
      throw std::runtime_error("cannot create replay chunk: " + path.string());
    hash = {};
    bytes = 0;
    append(header);
  }
  void append(const std::string &data) {
    put(file.get(), data);
    bytes += data.size();
    hash.add(data);
  }
  void seal() {
    sync(file.get());
    if (std::fclose(file.release()))
      throw std::runtime_error("replay chunk close failed");
    put(manifest, stream + "," + std::to_string(index) + "," +
                      chunkName(stream, index) + "," + std::to_string(bytes) +
                      "," + hash.finish() + "\n");
    sync(manifest);
  }
public:
  void start(const std::filesystem::path &dir, const std::string &name,
             const std::string &columns, FILE *inventory, uint64_t chunkLimit) {
    directory = dir;
    stream = name;
    header = columns;
    manifest = inventory;
    limit = chunkLimit;
    open();
  }
  void write(const std::string &data) {
    if (!file)
      throw std::runtime_error("replay chunk unavailable");
    if (data.size() > limit - header.size())
      throw std::runtime_error("CSV record exceeds chunk capacity");
    if (bytes + data.size() > limit) {
      seal();
      ++index;
      open();
    }
    append(data);
  }
  void flush(bool durable) {
    if (file) {
      if (durable)
        sync(file.get());
      else if (std::fflush(file.get()))
        throw std::runtime_error("replay chunk flush failed");
    }
  }
  void finish(bool complete) {
    if (file) {
      if (complete)
        seal();
      else if (std::fclose(file.release()))
        throw std::runtime_error("replay chunk close failed");
    }
  }
};
} // namespace replay
