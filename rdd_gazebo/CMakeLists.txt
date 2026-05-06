cmake_minimum_required(VERSION 3.8)
project(rdd_gazebo)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# 1. 의존성 패키지 찾아오기
find_package(ament_cmake REQUIRED)

# 2. 실행 및 설정 파일 설치 (이 부분이 핵심입니다!)
install(DIRECTORY
  launch
  config
  DESTINATION share/${PROJECT_NAME}
)

# 3. 테스트 환경 설정 (선택 사항)
if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
