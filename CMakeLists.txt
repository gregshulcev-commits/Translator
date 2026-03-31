cmake_minimum_required(VERSION 3.20)
project(pdf_word_translator_mvp LANGUAGES NONE)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

add_custom_target(run
    COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH=${CMAKE_SOURCE_DIR}/src ${Python3_EXECUTABLE} -m pdf_word_translator.app
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Run the MVP application"
)

add_custom_target(test
    COMMAND ${CMAKE_COMMAND} -E env PYTHONPATH=${CMAKE_SOURCE_DIR}/src ${Python3_EXECUTABLE} -m pytest
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
    COMMENT "Run automated tests"
)

configure_file(${CMAKE_SOURCE_DIR}/scripts/run_app.sh.in ${CMAKE_BINARY_DIR}/run_app.sh @ONLY)
file(CHMOD ${CMAKE_BINARY_DIR}/run_app.sh PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ GROUP_EXECUTE WORLD_READ WORLD_EXECUTE)

install(DIRECTORY src data docs tests tools scripts
        DESTINATION .
        PATTERN "__pycache__" EXCLUDE
        PATTERN ".pytest_cache" EXCLUDE)
install(FILES CMakeLists.txt README.md requirements.txt pytest.ini DESTINATION .)
