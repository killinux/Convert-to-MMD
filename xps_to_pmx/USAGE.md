# XPS to PMX 灵活映射系统 - 使用指南

## 快速开始

### 1. 导入 XPS 模型

在 Blender 中导入你的 XPS 模型（使用 XNALaraMesh 导入器）。

### 2. 打开映射编辑器面板

在 3D 视口右侧边栏找到 **"XPS to PMX Mapper"** 标签页，你会看到 4 个面板。

### 3. 四个工作步骤

#### 面板 ①：AUTO DETECTION（自动检测）

```
[ 🔍 Auto Detect Skeleton Type ]  ← 识别 XPS 骨骼类型
[ 🔄 Auto Map Bones ]              ← 自动映射所有骨骼
```

点击 **"Auto Map Bones"** 按钮，系统会：
- 分析你的 XPS 骨架结构
- 加载标准 XPS 映射预设
- 根据骨骼名称相似度计算置信度
- 生成初始映射配置

**输出示例：**
```
✓ Skeleton type: xps_standard
✓ Mapped 78 / 80 bones (97.5%)
⚠ 3 bones need manual attention
```

---

#### 面板 ②：MAPPING EDITOR（映射编辑器）

这里显示所有骨骼映射，以 XPS 名 → MMD 日文名 的格式。

**功能：**
- **搜索框**：快速查找特定骨骼
- **标签页**：按类型筛选（Spine/Arms/Legs/D-Bones/Other）
- **置信度**：显示自动检测的匹配度（越高越可信）
- **编辑**：点击任何映射项可编辑

**需要手动调整的情况：**
- 置信度 < 80% 的映射
- XPS 模型有非标准骨骼命名
- 遇到"需要手动检查"的警告

**示例：**
```
abdomenUpper   → 上半身       (99%) ✓
abdomenLower   → 上半身3      (98%) ✓
head           → 頭           (100%) ✓
leftArmElbow   → 左ひじ       (45%) ⚠️ 需要手动调整
```

---

#### 面板 ③：WEIGHT RULES（权重规则）

这里配置权重如何从 XPS 骨骼转移到 MMD 骨骼。

**四种主要规则类型：**

1. **FK → D-Bone**（FK 权重复制到 D-骨）
   - 例：左足 (FK) 的权重复制到 足D.L (D-骨)
   - 然后清零左足的权重（防止模型爆炸）
   - ⚠️ 这是 IK 系统的关键步骤

2. **Hip Blend Zone**（髋部混合区域）
   - 在大腿上部创建渐变过渡
   - 权重从纯 足D 逐渐过渡到 足D + 下半身
   - 比例：大腿上 46% 应用混合

3. **Twist Bone**（扭转骨梯度）
   - 腕捩、手捩等扭转骨的权重梯度
   - 接近中轴线的顶点权重多给主骨
   - 边缘顶点权重给扭转骨

4. **Normalize**（权重归一化）
   - 确保每个顶点的总权重 ≤ 1.0
   - 防止模型变形过度
   - 必须放在最后

**示例配置：**
```
▼ FK → D-Bone Rules
  ├─ 左足 → 足D.L (ratio: 1.0)
  ├─ 左ひざ → ひざD.L (ratio: 1.0)
  └─ 左足首 → 足首D.L (ratio: 1.0)

▼ Hip Blend Zone
  ├─ 足D.L ↔ 下半身 (blend: 0~46%)
  └─ 足D.R ↔ 下半身 (blend: 0~46%)

▼ Normalize
  └─ 所有顶点总权重 ≤ 1.0
```

---

#### 面板 ④：VALIDATION & PREVIEW（验证和预览）

最后一步：检查配置是否完整和正确。

**验证检查清单：**
```
☑ All required bones mapped           ← 必需的骨骼都有映射
☑ Parent-child relationships correct  ← 父子关系正确
☑ D-bone feedback chains valid        ← D-骨反馈链有效
☑ Hip zone blend fraction reasonable  ← 髋部混合比例合理
✗ IK chain joint count mismatch       ← IK 链关节数不匹配（有错误）
```

**数据表显示：**
- 所有映射的骨骼列表
- 每个骨骼的类型和映射对象
- 置信度评分

**层级树显示：**
```
▼ 全ての親
  ▼ センター (肩Y/リンク有)
    ▼ グルーブ
      ▼ 腰
        ▼ 下半身 [XPS: pelvis]
          ▼ 左足 [XPS: legLeftThigh]
            ▼ 左ひざ [XPS: legLeftKnee]
```

**操作按钮：**
```
[ 💾 Save Configuration ]   ← 保存配置为 JSON 文件
[ 📂 Load Preset ]         ← 加载已保存的预设
[ ▶ Start Conversion ]     ← 开始转换流程
```

---

## 完整工作流程示例

### 场景 1：标准 XPS 模型（快速路径）

```
1. 导入 XPS 模型，选中骨架
2. 打开 "XPS to PMX Mapper" 面板
3. 点击 [ 🔄 Auto Map Bones ]
4. 检查自动映射结果
   - 如果置信度都 > 95%，跳到第 6 步
   - 如果有低置信度项，进行第 5 步
5. 编辑映射（可选）
   - 在 ② MAPPING EDITOR 中修改有问题的映射
   - 确保所有骨骼都映射正确
6. 验证配置
   - 进入 ④ VALIDATION & PREVIEW 面板
   - 检查验证清单
   - 如果全绿色 ✓，可以开始转换
7. 开始转换
   - 点击 [ ▶ Start Conversion ]
   - 等待转换完成
```

### 场景 2：非标准 XPS 模型（手动调整路径）

```
1. 导入 XPS 模型，选中骨架
2. [ 🔄 Auto Map Bones ]
3. 在 ② MAPPING EDITOR 中逐一检查：
   - 所有骨骼是否正确映射？
   - 有没有遗漏的映射？
   - 有没有错误的映射？
4. 手动修正错误的映射
5. 保存配置
   - 点击 [ 💾 Save Configuration ]
   - 选择保存位置
   - 日后可以 [ 📂 Load Preset ] 重用
6. 验证 + 转换（同上）
```

---

## 高级：使用 JSON 预设

### 保存你的配置

一旦成功映射了一个 XPS 模型，你可以保存配置供以后使用：

```
[ 💾 Save Configuration ]
→ 输入文件名：my_xps_preset.json
→ 保存
```

### 加载已保存的预设

下次处理类似的 XPS 模型时：

```
[ 📂 Load Preset ]
→ 选择 my_xps_preset.json
→ 配置自动加载
```

### JSON 预设结构

```json
{
  "name": "My XPS Standard",
  "version": "1.0",
  "source_skeleton_type": "xps_standard",
  "bone_mappings": {
    "pelvis": {
      "xps_name": "pelvis",
      "mmd_name": "下半身",
      "confidence": 1.0,
      ...
    }
  },
  "weight_rules": [
    {
      "source_bone": "left_leg_thigh",
      "target_bone": "足D.L",
      "rule_type": "fk_to_d",
      ...
    }
  ]
}
```

---

## 常见问题

### Q: 自动检测的置信度很低，怎么办？

**A:** 这说明你的 XPS 模型可能有非标准的骨骼命名。手动编辑 ② MAPPING EDITOR 面板中的映射。按照以下原则：
- **脊椎骨**：pelvis → 下半身, chest → 上半身, head → 頭
- **腿骨**：leg → 足, knee → ひざ, ankle → 足首
- **手臂骨**：arm → 腕, shoulder → 肩

### Q: 权重规则太复杂了，有默认配置吗？

**A:** 有的！系统会自动为你生成权重规则：
1. FK → D-Bone（腿部权重复制）
2. Hip Blend Zone（髋部混合）
3. Normalize（权重归一化）

这是标准流程，适合大多数情况。

### Q: 转换后的模型权重不对，怎么调试？

**A:** 在 ④ VALIDATION & PREVIEW 面板中：
- 检查验证清单是否全通过
- 查看骨骼层级树是否正确
- 查看权重规则日志（转换后打印在 Blender 控制台）

如果需要深入调试，可以在 Blender Python 控制台运行：
```python
from xps_to_pmx import test_mapping_system
test_mapping_system.test_full_workflow()
```

### Q: 能支持其他格式的骨骼吗？比如 DAZ 或 Mixamo？

**A:** 可以！这个系统就是为了支持任何 XPS 变体。步骤：
1. 导入 DAZ/Mixamo 模型
2. 自动映射会尽力识别
3. 手动编辑不匹配的部分
4. 保存为新的预设
5. 以后可以直接加载这个预设

---

## 技术细节

### 映射置信度计算

```
置信度 = 字符串相似度 + 关键词匹配奖励
范围：0.0（完全不同）到 1.0（完全相同）

示例：
- "abdomenUpper" vs "abdomenUpper" → 1.0（完美匹配）
- "abdomenUpper" vs "abdomen" → 0.85（高度相似）
- "leftArm" vs "leftShoulder" → 0.65（部分相似）
- "misc123" vs "somebone" → 0.3（低相似度）
```

### 权重规则执行顺序

规则按以下顺序严格执行（**顺序很重要**）：

1. **FK → D-Bone**（复制 + 清零）
   - 必须先执行，为孤立骨转移做准备

2. **Hip Blend Zone**（渐变混合）
   - 依赖 D-骨已有权重

3. **Orphan Transfer**（孤立骨转移）
   - 处理未映射的辅助骨骼

4. **Normalize**（归一化）
   - 必须最后执行，调整所有权重

### 如何添加自定义规则

在 `mapping/detection.py` 的 `suggest_weight_rules()` 函数中添加：

```python
# 自定义规则示例
rule = data_structures.WeightMappingRule(
    source_bone="some_bone",
    target_bone="target_bone",
    transfer_ratio=0.5,
    zone="zone2",
    falloff_type="quadratic",  # 二次曲线梯度
    blend_threshold=0.5,
    rule_type="custom_type",  # 需要在 weights.py 中实现
    order=order_counter
)
config.weight_rules.append(rule)
```

---

## 故障排除

### 问题：部分骨骼映射失败

**解决：**
1. 在 ② MAPPING EDITOR 中找到失败的骨骼
2. 手动选择正确的 MMD 骨骼名
3. 点击保存或验证

### 问题：权重转移后模型变形

**解决：**
1. 检查 ③ WEIGHT RULES 中的规则顺序
2. 验证 FK → D-Bone 规则是否正确执行
3. 检查权重是否被正确清零

### 问题：转换过程中崩溃

**解决：**
1. 查看 Blender 控制台输出（Windows → Toggle System Console）
2. 检查是否有错误消息
3. 尝试简化映射（删除可选骨骼）

---

## 下一步

完成转换后，你可以：

1. **检查结果**
   - 在 Blender 中验证骨骼、权重和约束
   - 与参考 MMD 模型对比

2. **导出 PMX**
   - 使用 mmd_tools 导出为 .pmx 文件
   - 在 MMD 中打开验证

3. **优化权重**
   - 如果某些区域变形不对，可以手动调整权重
   - 使用 Blender 的权重绘制工具

4. **保存预设**
   - 如果这个 XPS 类型以后还会用到，保存预设
   - 分享给其他人使用

---

祝你转换顺利！🎉
