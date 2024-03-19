cmake_minimum_required(VERSION 3.5.0)
project(BinaryReceptor VERSION 0.1.0 LANGUAGES CXX C)

if (WIN32)
    list(APPEND BinaryReceptor_Sources
        src/windows/bluetooth.hpp
        src/windows/bluetooth.cpp
        src/windows/http.hpp
        src/windows/http.cpp
        src/windows/keypress.hpp
        src/windows/keypress.cpp
    )
endif()

if (LINUX)
    #TODO linux.
endif()

add_executable(BinaryReceptor
    ${BinaryReceptor_Sources}
    src/main.cpp
    src/mode.hpp
    src/util.hpp 
    src/util.cpp
    src/settings.hpp
    src/settings.cpp 
    src/starter.hpp 
    src/starter.cpp
)

target_include_directories(BinaryReceptor PRIVATE src)

if(WIN32)
    target_include_directories(BinaryReceptor PRIVATE src/windows)
    target_link_libraries(BinaryReceptor ws2_32 Bthprops)
    target_compile_definitions(BinaryReceptor PUBLIC WINDOWS)
endif()

if (LINUX)
    #TODO linux.
endif()
