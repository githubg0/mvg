set(LLVM_LINK_COMPONENTS support)

add_clang_executable(ac_parser
  ac_parser.cpp
  )
target_link_libraries(ac_parser
  PRIVATE
  clangTooling
  clangBasic
  clangASTMatchers
  )
