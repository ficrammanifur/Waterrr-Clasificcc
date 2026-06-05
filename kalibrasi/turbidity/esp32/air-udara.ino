const int turbidityPin = 32;

int nilaiDiAir = 4095;     // Nilai saat di air (jernih sempurna)
int nilaiDiUdara = 3031;   // Nilai saat di udara

void setup() {
  Serial.begin(115200);
  
  // Kalibrasi otomatis
  Serial.println("=== KALIBRASI SENSOR ===");
  Serial.println("1. Celupkan ke AIR, tekan tombol reset...");
  delay(3000);
  
  long totalAir = 0;
  for(int i = 0; i < 20; i++) {
    totalAir += analogRead(turbidityPin);
    delay(50);
  }
  nilaiDiAir = totalAir / 20;
  Serial.print("Nilai di AIR: ");
  Serial.println(nilaiDiAir);
  
  Serial.println("2. Angkat ke UDARA, tekan reset...");
  delay(3000);
  
  long totalUdara = 0;
  for(int i = 0; i < 20; i++) {
    totalUdara += analogRead(turbidityPin);
    delay(50);
  }
  nilaiDiUdara = totalUdara / 20;
  Serial.print("Nilai di UDARA: ");
  Serial.println(nilaiDiUdara);
  Serial.println("=== KALIBRASI SELESAI ===\n");
}

void loop() {
  int nilai = analogRead(turbidityPin);
  
  // BALIK LOGIKA: 
  // - Air jernih = nilai TINGGI (4095)
  // - Udara/keruh = nilai RENDAH (3031)
  int persenKekeruhan;
  
  if (nilai >= nilaiDiAir) {
    persenKekeruhan = 0;  // 0% keruh = 100% jernih
  } 
  else if (nilai <= nilaiDiUdara) {
    persenKekeruhan = 100; // 100% keruh
  } 
  else {
    // Map nilai ke persen keruh (inverted)
    persenKekeruhan = map(nilai, nilaiDiUdara, nilaiDiAir, 100, 0);
  }
  
  int persenKejernihan = 100 - persenKekeruhan;
  
  Serial.print("Nilai: ");
  Serial.print(nilai);
  Serial.print(" | Keruh: ");
  Serial.print(persenKekeruhan);
  Serial.print("% | Jernih: ");
  Serial.print(persenKejernihan);
  Serial.print("% | ");
  
  // Interpretasi kondisi
  if (persenKejernihan >= 80) {
    Serial.println("AIR SANGAT JERNIH");
  } 
  else if (persenKejernihan >= 50) {
    Serial.println("AIR CUKUP JERNIH");
  } 
  else if (persenKejernihan >= 20) {
    Serial.println("AIR AGAK KERUH");
  } 
  else {
    Serial.println("AIR KERUH / DI UDARA");
  }
  
  delay(500);
}
