cmake_minimum_required(VERSION 3.28)
project(GMOPass)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_VISIBILITY_PRESET hidden)
set(CMAKE_VISIBILITY_INLINES_HIDDEN 1)

find_package(LLVM REQUIRED CONFIG)
include(AddLLVM)

include_directories(${LLVM_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})

add_llvm_pass_plugin(GMOPass library.cpp)
set_target_properties(GMOPass PROPERTIES LINK_FLAGS_RELEASE -s)
target_compile_options(GMOPass PRIVATE -msse4.2)
target_compile_options(GMOPass PRIVATE -fno-exceptions)
target_compile_options(GMOPass PRIVATE -Wall -Wextra -Wpedantic -Wno-unused-parameter -Wno-unused-variable -Wno-unused-function -Wno-unused-value -Wno-missing-field-initializers)
