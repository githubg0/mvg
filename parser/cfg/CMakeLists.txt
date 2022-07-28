set(LLVM_LINK_COMPONENTS support)

add_clang_executable(cfg
  cfgGeneration.cpp
  )
target_link_libraries(cfg
  PRIVATE
  clangTooling
  clangBasic
  clangASTMatchers
  )
