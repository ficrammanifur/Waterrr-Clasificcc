<h1 align="center">💧 KLASIFIKASI KUALITAS AIR DENGAN MLP NEURAL NETWORK<br>
    <sub>Target Deployment di Raspberry Pi Pico 2 (Edge AI / TensorFlow Lite Micro)</sub>
</h1>

<p align="center">
  <img src="assets/pico2-preview.png" alt="Pico 2 Water Quality Monitor Preview" width="700"/>
</p>

<p align="center">
  <em>Sistem klasifikasi kualitas air berbasis Edge AI dengan MLP Neural Network pada Raspberry Pi Pico 2</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/last_commit-2026-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/language-Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/platform-RP2350-00ADD8?style=for-the-badge&logo=raspberrypi&logoColor=white" />
  <img src="https://img.shields.io/badge/framework-MicroPython-00979D?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/model-MLP%20Neural%20Network-FF6F00?style=for-the-badge&logo=tensorflow&logoColor=white" />
  <img src="https://img.shields.io/badge/sensors-4-informational?style=for-the-badge" />
  <img src="https://img.shields.io/badge/status-Selesai%20100%25-success?style=for-the-badge" />
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License: MIT" />
  </a>
</p>

---

## 📋 Daftar Isi
- [✨ Overview](#-overview)
- [🔧 Features](#-features)
- [📊 Struktur Notebook](#-struktur-notebook)
- [🎯 Tujuan Proyek](#-tujuan-proyek)
- [🧩 Komponen Hardware](#-komponen-hardware)
- [🤖 Model AI yang Dihasilkan](#-model-ai-yang-dihasilkan)
- [📱 Tampilan OLED](#-tampilan-oled)
- [⚙️ Instalasi](#️-instalasi)
- [🚀 Cara Menjalankan](#-cara-menjalankan)
- [📊 Hasil Pengujian](#-hasil-pengujian)
- [📁 Struktur File](#-struktur-file)
- [🐞 Troubleshooting](#-troubleshooting)
- [📄 Lisensi](#-lisensi)

---

## ✨ Overview

**Klasifikasi Kualitas Air dengan MLP Neural Network** adalah sistem monitoring kualitas air berbasis **Edge AI** yang menggunakan **Raspberry Pi Pico 2 (RP2350)** dengan **MicroPython**. Sistem ini memanfaatkan **MLP Neural Network** untuk mengkalibrasi sensor pH dan TDS, serta mengklasifikasikan kelayakan air.

### 🎯 Tujuan Utama
1. **Kalibrasi sensor pH dan TDS** menggunakan model regresi MLP
2. **Klasifikasi kelayakan air** (LAYAK / TIDAK LAYAK)
3. **Identifikasi 9 jenis air** (multi-class classification)
4. **Implementasi Edge AI** pada Raspberry Pi Pico 2
5. **Tampilan hasil** pada OLED 128x64

### 🎯 Cara Kerja
1. **Training Model** → Dilakukan di Google Colab menggunakan dataset 12.002 data
2. **Export TFLite** → Model dikonversi ke TensorFlow Lite Micro
3. **Deploy ke Pico 2** → Upload file TFLite ke Pico 2
4. **Baca Sensor** → ADC membaca sinyal dari sensor pH, TDS, Turbidity
5. **Prediksi** → Model AI memprediksi pH, TDS, kelayakan, dan jenis air
6. **Tampilkan OLED** → Hasil ditampilkan di layar OLED 128x64

---

## 🔧 Features

| Fitur | Keterangan |
|-------|------------|
| ✅ **3 Model AI** | Regresi (pH & TDS), Binary, Multi-Class |
| ✅ **9 Jenis Air** | AIR ALKALI, AIR MATANG/DISPENSER, AIR MINERAL, Air Mentah, Keruh/Organik, RO/DEMINERAL, TDS Ekstrem, Tercemar Asam, Tercemar Basa |
| ✅ **Kalibrasi Sensor** | pH 3-point interpolation, TDS DFRobot formula |
| ✅ **Stabilisasi 10-15 detik** | Rata-rata pembacaan sensor |
| ✅ **OLED Display** | 128x64 I2C SSD1306 |
| ✅ **Akurasi Tinggi** | Binary 100%, Multi-Class 95.19% |
| ✅ **Ukuran Kecil** | Total model < 50 KB |

---

## 📊 Struktur Notebook

| **Fase** | **Judul** | **Cell** | **Status** | **Keterangan** |
|----------|-----------|----------|------------|----------------|
| 1 | Dataset Upload & Merging | 1.1, 1.2 | ✅ Selesai | Upload dan gabung dataset |
| 2 | Data Preprocessing & Cleaning | 2.1 | ✅ Selesai | Bersihkan data, fix PPT garam |
| 3 | Smart Relabeling & Encoding | 3.1 | ✅ Selesai | Kategorisasi ulang jenis air |
| 4 | Exploratory Data Analysis | 4.1 | ✅ Selesai | Visualisasi korelasi sensor |
| 5 | AI Calibration (Regression) | 5.1 - 5.5 | ✅ Selesai | Model kalibrasi pH & TDS |
| 6 | Binary Classification | 6.1 - 6.3 | ✅ Selesai | Model kelayakan Layak/Tidak |
| 7 | Multi-Class Classification | 7.1 - 7.3 | ✅ Selesai | Model 9 jenis air |
| 8 | Feature Fusion & Scaling | 8.1 | ✅ Selesai | Ekspor parameter scaling |
| 9 | Anomaly Detection | 9.1 - 9.2 | ✅ Selesai | Autoencoder deteksi anomali |
| 10 | TFLite Model Export | 10.1 - 10.7 | ✅ Selesai | Konversi 3 model + generate kode Pico 2 + ZIP |

**Total: 10 Fase, 30+ Code Cell, Selesai 100%** ✅

---

## 🧩 Komponen Hardware

| Komponen | Fungsi | Pin Pico 2 |
|----------|--------|------------|
| **Raspberry Pi Pico 2 (RP2350)** | Otak utama sistem | - |
| **Sensor pH** | Mengukur pH air | GP26 (ADC0) |
| **Sensor TDS** | Mengukur TDS | GP27 (ADC1) |
| **Sensor Turbidity** | Mengukur kekeruhan | GP28 (ADC2) |
| **DS18B20** | Mengukur suhu air | GP16 (1-Wire) |
| **OLED SSD1306** | Tampilan hasil | GP6 (SDA), GP7 (SCL) |
| **LED Internal** | Indikator komputasi | GP25 |

### Diagram Wiring
```
Raspberry Pi Pico 2
├─ GP26 (ADC0) ──── pH Sensor (Analog)
├─ GP27 (ADC1) ──── TDS Sensor (Analog)
├─ GP28 (ADC2) ──── Turbidity Sensor (Analog)
├─ GP16 ─────────── DS18B20 (1-Wire)
├─ GP6 (SDA) ────── OLED SSD1306 (I2C)
├─ GP7 (SCL) ────── OLED SSD1306 (I2C)
├─ GP25 ─────────── LED Internal
├─ 3.3V ─────────── Sensor VCC
└─ GND ──────────── Sensor GND
```

---

## 🤖 Model AI yang Dihasilkan

| Model | Fungsi | Arsitektur | Akurasi | Ukuran TFLite |
|-------|--------|------------|---------|---------------|
| **Regresi** | Kalibrasi pH & TDS | 4 layer (128-64-32-2) | MAE: 0.692 (pH), 31.4 ppm (TDS) | 19.09 KB |
| **Binary** | Klasifikasi kelayakan | 4 layer (64-32-16-1) | **100%** | 8.57 KB |
| **Multi-Class** | 9 jenis air | 4 layer (128-64-32-9) | **95.19%** | 17.92 KB |
| **Autoencoder** | Deteksi anomali | 4 layer (8-2-8-4) | Threshold: 0.0227 | - |

### 9 Jenis Air yang Dikenali
```
0: AIR ALKALI
1: AIR MATANG / DISPENSER
2: AIR MINERAL
3: Air Mentah
4: Keruh/Organik
5: RO / DEMINERAL
6: TDS Ekstrem (Garam)
7: Tercemar Asam (Cuka)
8: Tercemar Basa (Kapur)
```

---

## 📱 Tampilan OLED

### Splash Screen (Saat Boot)
```
┌────────────────────────────────────────────┐
│                                            │
│          Water Monitor                     │
│             Quality                        │
│                                            │
└────────────────────────────────────────────┘
```

### Stabilisasi (10-15 detik)
```
┌────────────────────────────────────────────┐
│          Membaca...                        │
│              8s                            │
│  pH:7.50          TDS:45                  │
└────────────────────────────────────────────┘
```

### Hasil (LAYAK)
```
┌────────────────────────────────────────────┐
│  pH:7.85   |   ppm:46                     │
│                                            │
│             LAYAK                          │
│                                            │
│  ────────────────────────────────────────  │
│  100%            25.0C                    │
└────────────────────────────────────────────┘
```

### Hasil (TIDAK LAYAK)
```
┌────────────────────────────────────────────┐
│  pH:3.94   |   ppm:140                    │
│                                            │
│           TIDAK LAYAK                      │
│                                            │
│  ────────────────────────────────────────  │
│  45%             25.0C                    │
└────────────────────────────────────────────┘
```

---

## ⚙️ Instalasi

### 1. Clone Repository
```bash
git clone https://github.com/ficrammanifur/Waterrr-Clasificcc.git
cd Waterrr-Clasificcc
```

### 2. Upload Firmware MicroPython ke Pico 2
```bash
# Download firmware terbaru
wget https://micropython.org/download/rp2-pico-2/rp2-pico-2-latest.uf2

# Copy ke Pico 2 (mode bootloader)
sudo cp rp2-pico-2-latest.uf2 /media/rban/RP2350/
```

### 3. Upload File ke Pico 2

#### Menggunakan Thonny (Rekomendasi)
1. Buka Thonny
2. **Run** → **Select interpreter** → **MicroPython (Raspberry Pi Pico)**
3. **View** → **Files**
4. Drag & drop file:
   - `main.py`
   - `ssd1306.py`
   - `model_regression.tflite`
   - `model_binary.tflite`
   - `model_multi.tflite`

#### Menggunakan mpremote
```bash
mpremote connect /dev/ttyACM0 cp main.py :
mpremote connect /dev/ttyACM0 cp ssd1306.py :
mpremote connect /dev/ttyACM0 cp model_regression.tflite :
mpremote connect /dev/ttyACM0 cp model_binary.tflite :
mpremote connect /dev/ttyACM0 cp model_multi.tflite :
```

---

## 🚀 Cara Menjalankan

### 1. Hubungkan Hardware
```
Pastikan semua sensor terhubung sesuai diagram wiring
```

### 2. Jalankan Program
```bash
# Di Thonny: buka main.py → klik Run (F5)
# Atau di terminal:
mpremote connect /dev/ttyACM0 run main.py
```

### 3. Proses Pembacaan
```
1. Splash screen muncul 1.5 detik
2. Stabilisasi 10-15 detik (rata-rata sensor)
3. Hasil ditampilkan di OLED dan Serial Monitor
4. Program berhenti (single read) → Reset untuk baca ulang
```

---

## 📊 Hasil Pengujian

### 📋 Tabel Pengujian Error Sensor (Hari 1 - 5)

#### **Pengujian Hari ke-1 (Deploy)**
| Parameter | Nilai Tester | Nilai Pico 2 | Error | Status |
|-----------|--------------|--------------|-------|--------|
| pH | 8.20 | 7.85 | 0.35 | ✅ Baik |
| TDS (ppm) | 129 | 140 | 11 | ✅ Baik |
| NTU | 0.5 | 0.8 | 0.3 | ✅ Baik |
| Suhu (°C) | 29.5 | 29.3 | 0.2 | ✅ Baik |
| Kelayakan | LAYAK | LAYAK | - | ✅ Sesuai |

#### **Pengujian Hari ke-2**
| Parameter | Nilai Tester | Nilai Pico 2 | Error | Status |
|-----------|--------------|--------------|-------|--------|
| pH | 8.35 | 8.10 | 0.25 | ✅ Baik |
| TDS (ppm) | 148 | 155 | 7 | ✅ Baik |
| NTU | 0.3 | 0.5 | 0.2 | ✅ Baik |
| Suhu (°C) | 29.8 | 29.6 | 0.2 | ✅ Baik |
| Kelayakan | LAYAK | LAYAK | - | ✅ Sesuai |

#### **Pengujian Hari ke-3**
| Parameter | Nilai Tester | Nilai Pico 2 | Error | Status |
|-----------|--------------|--------------|-------|--------|
| pH | 8.02 | 7.75 | 0.27 | ✅ Baik |
| TDS (ppm) | 6 | 12 | 6 | ✅ Baik |
| NTU | 0.2 | 0.3 | 0.1 | ✅ Baik |
| Suhu (°C) | 29.2 | 29.0 | 0.2 | ✅ Baik |
| Kelayakan | LAYAK | LAYAK | - | ✅ Sesuai |

#### **Pengujian Hari ke-4**
| Parameter | Nilai Tester | Nilai Pico 2 | Error | Status |
|-----------|--------------|--------------|-------|--------|
| pH | 8.65 | 8.40 | 0.25 | ✅ Baik |
| TDS (ppm) | 86 | 92 | 6 | ✅ Baik |
| NTU | 0.4 | 0.6 | 0.2 | ✅ Baik |
| Suhu (°C) | 30.1 | 29.9 | 0.2 | ✅ Baik |
| Kelayakan | LAYAK | LAYAK | - | ✅ Sesuai |

#### **Pengujian Hari ke-5**
| Parameter | Nilai Tester | Nilai Pico 2 | Error | Status |
|-----------|--------------|--------------|-------|--------|
| pH | 8.33 | 8.05 | 0.28 | ✅ Baik |
| TDS (ppm) | 170 | 178 | 8 | ✅ Baik |
| NTU | 0.5 | 0.7 | 0.2 | ✅ Baik |
| Suhu (°C) | 30.5 | 30.2 | 0.3 | ✅ Baik |
| Kelayakan | LAYAK | LAYAK | - | ✅ Sesuai |

### 📊 Ringkasan Error 5 Hari

| Parameter | Error Min | Error Max | Error Rata-rata | Keterangan |
|-----------|-----------|-----------|-----------------|------------|
| **pH** | 0.25 | 0.35 | **0.28** | ✅ Sangat Baik |
| **TDS (ppm)** | 6 | 11 | **7.6** | ✅ Sangat Baik |
| **NTU** | 0.1 | 0.3 | **0.2** | ✅ Sangat Baik |
| **Suhu (°C)** | 0.2 | 0.3 | **0.22** | ✅ Sangat Baik |
| **Kelayakan** | 100% | 100% | **100%** | ✅ Sempurna |

---

### 📊 Tabel Perbandingan Model

| Model | Akurasi | MAE | R² | Ukuran |
|-------|---------|-----|-----|--------|
| **Regresi pH** | - | 0.692 | - | 19.09 KB |
| **Regresi TDS** | - | 31.4 ppm | - | 19.09 KB |
| **Binary Classification** | **100%** | - | - | 8.57 KB |
| **Multi-Class** | **95.19%** | - | - | 17.92 KB |
| **Autoencoder** | - | - | - | - |

---

## 📁 Struktur File

```text
Waterrr-Clasificcc/
├── 📄 main.py                     # Program utama Pico 2
├── 📄 ssd1306.py                  # Driver OLED SSD1306
├── 📄 model_regression.tflite     # Model kalibrasi pH & TDS
├── 📄 model_binary.tflite         # Model klasifikasi kelayakan
├── 📄 model_multi.tflite          # Model klasifikasi 9 jenis air
├── 📄 README.md                   # Dokumentasi proyek
├── 📁 colab/
│   ├── 📄 klasifikasi_air.ipynb   # Notebook training model
│   └── 📄 dataset_mlp.csv         # Dataset training
├── 📁 test/
│   ├── 📄 ph_test.py              # Test sensor pH
│   ├── 📄 tds_test.py             # Test sensor TDS
│   ├── 📄 turbidity_test.py       # Test sensor turbidity
│   └── 📄 i2c_scan.py             # Scan I2C devices
└── 📁 assets/
    ├── 🖼️ pico2-preview.png
    ├── 🖼️ oled-display.jpg
    └── 🖼️ wiring-diagram.png
```

---

## 🐞 Troubleshooting

### OLED Error (EIO)
| Masalah | Solusi |
|---------|--------|
| OLED tidak terdeteksi | Cek koneksi SDA/GP6, SCL/GP7 |
| Alamat I2C salah | Jalankan `i2c.scan()` cek alamat 0x3C |
| Power tidak cukup | Pastikan VCC 3.3V |

### Sensor pH 14.00
| Masalah | Solusi |
|---------|--------|
| Sensor tidak terhubung | Cek kabel BNC |
| Voltase pH rendah | Kalibrasi ulang V4, V7, V9 |
| Modul pH mati | Cek power 5V |

### TDS Error
| Masalah | Solusi |
|---------|--------|
| TDS terlalu tinggi | Rekalibrasi slope TDS |
| TDS 0 | Periksa koneksi sensor |
| Nilai tidak stabil | Tambah sampling (100x) |

### Program Tidak Berjalan
| Masalah | Solusi |
|---------|--------|
| File hilang | Upload ulang semua file |
| Memory penuh | Hapus file tidak perlu |
| Firmware outdated | Update MicroPython |

---

## 📄 Lisensi

Proyek ini open source di bawah lisensi **MIT**.

```text
MIT License

Copyright (c) 2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
```

---

<div align="center">

**💧 KLASIFIKASI KUALITAS AIR DENGAN MLP NEURAL NETWORK**  
**Powered by Raspberry Pi Pico 2 • Edge AI • MicroPython**

⭐ **Star this repo if you like it!**

<p><a href="#top">⬆ Kembali ke Atas</a></p>

</div>
