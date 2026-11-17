import pytest

from game.camera_rig import (
    spring_arm,
    smooth_return,
    project_shoulder,
    fov_for_speed,
    dynamic_near,
    average_normals
)


def test_spring_no_hit():
    assert spring_arm((0.0, 0.0, 0.0), (0.0, 0.0, 10.0), 5.0, 100.0, 0.5) == (0.0, 0.0, 5.0)

def test_spring_hit():
    assert spring_arm((0.0, 0.0, 0.0), (0.0, 0.0, 10.0), 5.0, 2.0, 0.5) == (0.0, 0.0, 1.5)

def test_spring_hit_zero():
    assert spring_arm((0.0, 0.0, 0.0), (0.0, 0.0, 10.0), 5.0, 0.0, 0.5) == (0.0, 0.0, 0.0)

def test_smooth_moves():
    assert smooth_return(0.0, 10.0, 0.1, 5.0) == pytest.approx(0.5)

def test_smooth_clamps():
    assert smooth_return(9.8, 10.0, 0.1, 5.0) == 10.0

def test_smooth_zero_dt():
    assert smooth_return(0.0, 10.0, 0.0, 5.0) == 0.0

def test_shoulder_projected_out():
    assert project_shoulder((1.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.0, 0.0, 0.0)) == (0.0, 0.0, 0.0)

def test_shoulder_tangent_kept():
    assert project_shoulder((0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)) == (0.0, 1.0, 0.0)

def test_fov_base():
    assert fov_for_speed(60.0, 0.0, 90.0) == 60.0

def test_fov_speed():
    assert fov_for_speed(60.0, 10.0, 90.0) == 80.0

def test_fov_clamps():
    assert fov_for_speed(60.0, 20.0, 90.0) == 90.0

def test_near_hit():
    assert dynamic_near(1.0, 0.5) == 0.5

def test_near_min():
    assert dynamic_near(0.01, 0.1) == 0.05

def test_normals_same():
    assert average_normals([(1.0, 0.0, 0.0), (1.0, 0.0, 0.0)]) == (1.0, 0.0, 0.0)

def test_normals_opposite():
    assert average_normals([(1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)]) == (0.0, 0.0, 0.0)
