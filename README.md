# 📡 Zhihuifangdong for Home Assistant

一个非官方的 [智慧房东](https://www.zhihuifangdong.net/) 电表集成，支持在 Home Assistant 中查看电表的余额、电量、功率、电压、电流等信息。

⚠️ **免责声明**：本集成基于抓包接口开发，仅供学习和个人使用，请勿用于商业用途。

---

## ✨ 功能

* 显示电表余额（金额）
* 显示剩余电量（kWh）
* 显示电价（元/kWh）
* 显示剩余天数预测
* 传感器：电压、电流、功率（由于电表每小时上传一次数据，故每30分钟更新一次）
* 支持多个电表（自动检测 ID）

---

## 📦 安装方式

### HACS (推荐)

1. 打开 Home Assistant → HACS → 集成 → 右上角菜单 → **自定义存储库**
2. 添加仓库地址：

   ```
   https://github.com/findyy99/homeassistant-zhihuifangdong
   ```

   类型选择 **集成**
3. 在 HACS 中搜索并安装 **Zhihuifangdong**
4. 重启 Home Assistant

### 手动安装

1. 下载 `custom_components/zhihuifangdong/` 文件夹
2. 拷贝到你的 HA 配置目录下：

   ```
   config/custom_components/zhihuifangdong/
   ```
3. 重启 Home Assistant

### 查看实体
然后重启 Home Assistant，即可在 **实体列表** 中看到如下传感器（基于前一个小时的数据）：

* `sensor.zhihuifangdong_electricity` → 电表剩余电量
* `sensor.zhihuifangdong_voltage` → 电压
* `sensor.zhihuifangdong_current` → 电流
* `sensor.zhihuifangdong_power` → 功率

### 能源面板支持 ✅

新增一个累计用电量传感器：`sensor.zhihuifangdong_electricEnergy`（单位 kWh），
该传感器使用 **device_class=energy** 和 **state_class=total_increasing**，可在 Home Assistant 的 **能源 (Energy)** 配置中被识别并选择用于计算耗电量与费用。

如何查看“今天 / 本月”用电量：
- 在能源面板中选择该用电量传感器，Home Assistant 会基于长期统计显示日/月消耗。
- 如果你想要明确的“每日/每月”读数，也可以使用 `utility_meter` 集成为该传感器建立按日或按月重置的计量表（示例：`utility_meter.daily` 或 `utility_meter.monthly`）。

示例（configuration.yaml）:

```yaml
utility_meter:
   zhihuifangdong_daily:
      source: sensor.zhihuifangdong_electricEnergy
      cycle: daily

   zhihuifangdong_monthly:
      source: sensor.zhihuifangdong_electricEnergy
      cycle: monthly
```

然后在实体列表里添加 `sensor.zhihuifangdong_electricEnergy` 或对应的 utility_meter 实体到能源面板中。

---

## 🛠️ 计划支持

* 自动预测每日耗电量（基于天气 & 历史功率数据）
* 更多电费分析面板

---

## 🤝 贡献

欢迎提交 PR 或 issue，一起完善功能。

---

## 📜 许可证

Apache License