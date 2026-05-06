cmake_minimum_required(VERSION 3.8)
project(rdd_description)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

# -----------------------------------------------------------------------
# 여기에 설치 규칙을 추가합니다.
# -----------------------------------------------------------------------
install(DIRECTORY
  config
  launch
  rviz
  urdf
  worlds
  meshes

  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/rdd_caster_sync.py
  scripts/rdd_caster_state_pub.py
  scripts/rdd_joint_state_filter.py
  scripts/rdd_keyboard_teleop.py
  scripts/rdd_load_sync.py
  scripts/rdd_nav2_cmd_vel_bridge.py
  DESTINATION lib/${PROJECT_NAME}
)
# -----------------------------------------------------------------------

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
