"""Third-person camera rig building blocks.

The rig avoids wall clipping with a sphere/multi-ray spring-arm sweep, eases
the camera back with a damped constant-speed return, projects the shoulder
offset onto the wall tangent plane, clamps the speed-driven FOV curve, grows
the near clip when the camera is pressed against geometry, and resolves
several colliders by trusting the nearest hit's normal instead of averaging
conflicting normals.
"""

import math

# FOV widening in degrees per unit of speed.
FOV_GAIN_PER_SPEED = 2.0

# The dynamic near plane is never smaller than this fraction of the
# configured near plane, keeping depth precision usable.
NEAR_FLOOR_FACTOR = 0.5


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(v, s):
    return (v[0] * s, v[1] * s, v[2] * s)


def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _length(v):
    return math.sqrt(_dot(v, v))


def _normalize(v):
    length = _length(v)
    if length <= 1e-12:
        return (0.0, 0.0, 0.0)
    return _scale(v, 1.0 / length)


def _nearest_hit(hit_distances):
    """Collapse sphere-sweep / multi-ray results to the shortest hit.

    Accepts a scalar distance or an iterable. Non-finite values and
    negative distances mean "no hit" and are ignored. When every probe
    misses, infinity is returned so the caller falls back to full arm length.
    """
    if isinstance(hit_distances, (int, float)):
        candidates = [float(hit_distances)]
    else:
        candidates = []
        for hit in hit_distances:
            # A (normal, distance) probe result is also tolerated.
            if isinstance(hit, (tuple, list)) and len(hit) == 2 and \
                    isinstance(hit[0], (tuple, list)):
                hit = hit[1]
            candidates.append(float(hit))

    nearest = math.inf
    for distance in candidates:
        if math.isfinite(distance) and distance >= 0.0:
            nearest = min(nearest, distance)
    return nearest


def spring_arm(origin, camera_target, arm_length, hit_distance, radius):
    """Sphere-sweep spring arm.

    ``origin`` is the pivot (character head), ``camera_target`` defines the
    arm direction, ``arm_length`` is the rest length, ``hit_distance`` is a
    scalar distance or a collection of probe distances (multi-ray / sphere
    sweep) and ``radius`` is the camera collision sphere radius.

    The shortest probe wins so thin pillars between the character and the
    wall can no longer be missed by a single ray. The camera stops
    ``radius`` before the surface and is never placed behind the pivot.
    """
    offset = _sub(camera_target, origin)
    length = _length(offset)
    if length <= 1e-12:
        return tuple(origin)
    direction = _scale(offset, 1.0 / length)

    nearest = _nearest_hit(hit_distance)
    allowed = min(float(arm_length), max(0.0, nearest - float(radius)))
    return tuple(_add(origin, _scale(direction, allowed)))


def smooth_return(current, target, dt, rate):
    """Move ``current`` toward ``target`` at constant ``rate`` per second.

    A constant approach speed gives a predictable lag/hysteresis instead of
    snapping the camera instantly. The move is clamped at the target so the
    camera never overshoots, and a zero (or negative) delta time leaves the
    value untouched.
    """
    delta = float(target) - float(current)
    if dt <= 0.0 or delta == 0.0:
        return float(current)

    step = float(rate) * float(dt)
    if step >= abs(delta):
        return float(target)
    return float(current) + math.copysign(step, delta)


def project_shoulder(shoulder_offset, collision_normal, original_direction):
    """Project the shoulder offset onto the wall tangent plane.

    When the camera is pressed against geometry, the component of the
    shoulder offset pointing into the wall (along ``collision_normal``) is
    removed, which stops the camera from being driven into the character's
    head. Tangent components are preserved. A degenerate normal means there
    is no collision plane, so the offset is returned unchanged.

    ``original_direction`` is accepted for API symmetry with the rig's
    assembly code; the projection itself is defined purely by the offset
    and the surface normal.
    """
    normal_length_sq = _dot(collision_normal, collision_normal)
    if normal_length_sq <= 1e-12:
        return tuple(shoulder_offset)

    penetration = _dot(shoulder_offset, collision_normal) / normal_length_sq
    return tuple(_sub(shoulder_offset, _scale(collision_normal, penetration)))


def fov_for_speed(base_fov, speed, max_fov):
    """Widen FOV with speed, clamped to ``[base_fov, max_fov]``.

    The linear speed curve is hard-clamped so sprinting cannot distort the
    frame beyond ``max_fov``, and reverse/slow motion never narrows the
    view below the base FOV.
    """
    desired = float(base_fov) + FOV_GAIN_PER_SPEED * float(speed)
    return max(float(base_fov), min(float(max_fov), desired))


def dynamic_near(hit_distance, normal_near):
    """Choose the near clip plane from the nearest surface distance.

    Pulling the near plane toward the camera-facing surface prevents the
    camera from seeing inside a wall when pinned against it, while the
    lower bound (half the configured near plane) preserves depth-buffer
    precision and the upper bound keeps the normal setting in open space.
    """
    floor_near = float(normal_near) * NEAR_FLOOR_FACTOR
    return min(float(normal_near), max(floor_near, float(hit_distance)))


def average_normals(hits):
    """Resolve contact normals from several colliders.

    Averaging opposing normals cancels to zero and makes the camera jitter
    between colliders. Instead:

    * Probe results carrying a distance, ``(normal, distance)``, select the
      normal of the *shortest-distance* hit — the surface actually pushing
      the camera.
    * Bare normal vectors are averaged and normalized, which still yields
      the zero vector for exactly opposing normals.
    """
    if not hits:
        return (0.0, 0.0, 0.0)

    weighted = None
    vectors = []
    for hit in hits:
        if isinstance(hit, (tuple, list)) and len(hit) == 2 and \
                isinstance(hit[0], (tuple, list)):
            normal, distance = hit
            if weighted is None or distance < weighted[1]:
                weighted = (normal, distance)
        else:
            vectors.append(hit)

    if weighted is not None and not vectors:
        return _normalize(weighted[0])

    if weighted is not None:
        vectors = vectors + [weighted[0]]

    summed = (0.0, 0.0, 0.0)
    for normal in vectors:
        summed = _add(summed, normal)
    averaged = _scale(summed, 1.0 / len(vectors))
    return _normalize(averaged)
