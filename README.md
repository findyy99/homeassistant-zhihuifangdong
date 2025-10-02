# 📡 Zhihuifangdong for Home Assistant

一个非官方的 [智慧房东](https://api.zhihuifangdong.net) 电表集成，支持在 Home Assistant 中查看电表的余额、电量、功率、电压、电流等信息。

⚠️ **免责声明**：本集成基于抓包接口开发，仅供学习和个人使用，请勿用于商业用途。

---

## ✨ 功能

* 显示电表余额（金额）
* 显示剩余电量（kWh）
* 显示电价（元/kWh）
* 显示剩余天数预测
* 传感器：电压、电流、功率（每30分钟更新一次）
* 支持多个电表（自动检测 ID）

---

## 📦 安装方式

### HACS (推荐)

1. 打开 Home Assistant → HACS → 集成 → 右上角菜单 → **自定义存储库**
2. 添加仓库地址：

   ```
   https://github.com/findyy99/ha-zhihuifangdong
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

---

## ⚙️ 配置方法

安装完成后，在 `configuration.yaml` 中添加：

```yaml
sensor:
  - platform: zhihuifangdong
    username: "你的账号"
    password: "你的密码"
```

然后重启 Home Assistant，即可在 **实体列表** 中看到如下传感器：

* `sensor.zhihuifangdong_electricity` → 剩余电量
* `sensor.zhihuifangdong_voltage` → 电压
* `sensor.zhihuifangdong_current` → 电流
* `sensor.zhihuifangdong_power` → 功率

---

## 🛠️ 计划支持

* 自动预测每日耗电量（基于天气 & 历史功率数据）
* 更多电费分析面板

---

## 🤝 贡献

欢迎提交 PR 或 issue，一起完善功能。

---

## 📜 许可证

MIT License