set(LLVM_LINK_COMPONENTS support)

add_clang_executable(rewriter
  rewriter.cpp
  )
target_link_libraries(rewriter
  PRIVATE
  clangTooling
  clangBasic
  clangASTMatchers
  )
