# pairwise-camera-rig

第三人称游戏镜头一贴墙就穿模：弹簧臂只做一条射线，角色和墙之间的细柱子被漏掉；碰撞后相机瞬间弹回，没有做平滑和滞后；shoulder offset 在贴墙时仍然加在错误方向，镜头卡进角色头里；FOV 随速度变化但没有上限，冲刺时画面畸变；near clip 太小，贴墙时看到墙内；相机被多个碰撞体推挤时法线平均错误，镜头抖动。game/camera_rig.py 是核心，tests/test_camera_rig.py 15个红。要修的是：用球形/多射线扫描；碰撞回退加阻尼；shoulder offset 按碰撞法线修正；FOV 曲线 clamp；动态 near clip；多碰撞法线按最短距离取。

## 运行

```bash
python -m pytest tests -q
```

初始状态：15 个用例失败。修复实现使全部用例通过，不要修改 `tests/` 下的测试。

语言/框架：Python 3, pytest；环境可复现等级：无外部依赖。
