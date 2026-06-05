const int turbidityPin = 32;

// Nilai threshold berdasarkan data valid Anda
const int nilaiJernihMaks = 4095;    // Air sangat jernih
const int nilaiKeruhMin = 2900;      // Air keruh / udara (dari data: 2495-2901)

void setup() {
  Serial.begin(115200);
  Serial.println("=== Sensor Kekeruhan Air ===");
  Serial.println("========================================");
}

void loop() {
  int nilai = analogRead(turbidityPin);
  float tegangan = (nilai / 4095.0) * 3.3;
  
  // Hitung persen kekeruhan (0% = jernih, 100% = keruh)
  int persenKekeruhan;
  
  if (nilai >= nilaiJernihMaks) {
    persenKekeruhan = 0;
  } 
  else if (nilai <= nilaiKeruhMin) {
    persenKekeruhan = 100;
  } 
  else {
    // Mapping linear: 2900 = 100% keruh, 4095 = 0% keruh
    persenKekeruhan = map(nilai, nilaiKeruhMin, nilaiJernihMaks, 100, 0);
  }
  
  int persenKejernihan = 100 - persenKekeruhan;
  
  // Tampilkan output
  Serial.print("Nilai ADC: ");
  Serial.print(nilai);
  Serial.print(" | Volt: ");
  Serial.print(tegangan, 1);
  Serial.print(" | Keruh: ");
  Serial.print(persenKekeruhan);
  Serial.print("% | Jernih: ");
  Serial.print(persenKejernihan);
  Serial.print("% | ");
  
  // Interpretasi kondisi berdasarkan data Anda
  if (nilai <= 2900) {
    Serial.println("AIR SANGAT KERUH");
  } 
  else if (nilai <= 3200) {
    Serial.println("AIR KERUH");
  }
  else if (nilai <= 3500) {
    Serial.println("DI UDARA");
  }
  else if (nilai <= 3800) {
    Serial.println("AIR KERUH");
  }
  else if (nilai <= 4000) {
    Serial.println("AIR JERNIH");
  }
  else {
    Serial.println("AIR SANGAT JERNIH");
  }
  
  delay(500);
}
