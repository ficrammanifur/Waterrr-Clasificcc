const int turbidityPin = 32;

// Set nilai threshold manual berdasarkan data Anda
const int nilaiJernih = 4000;   // Nilai untuk air sangat jernih
const int nilaiKeruh = 3000;    // Nilai untuk air keruh/udara

void setup() {
  Serial.begin(115200);
  Serial.println("=== Sensor Kekeruhan Air ===");
}

void loop() {
  int nilai = analogRead(turbidityPin);
  float tegangan = (nilai / 4095.0) * 3.3;
  
  // Hitung persen kekeruhan
  int persenKekeruhan;
  
  if (nilai >= nilaiJernih) {
    persenKekeruhan = 0;
  } 
  else if (nilai <= nilaiKeruh) {
    persenKekeruhan = 100;
  } 
  else {
    persenKekeruhan = map(nilai, nilaiKeruh, nilaiJernih, 100, 0);
  }
  
  int persenKejernihan = 100 - persenKekeruhan;
  
  // Output format sesuai permintaan
  Serial.print("Nilai ADC: ");
  Serial.print(nilai);
  Serial.print(" | Volt: ");
  Serial.print(tegangan, 1);
  Serial.print(" | Keruh: ");
  Serial.print(persenKekeruhan);
  Serial.print("% | Jernih: ");
  Serial.print(persenKejernihan);
  Serial.print("% | ");
  
  if (nilai <= 3100) {
    Serial.println("AIR KERUH / DI UDARA");
  } 
  else if (nilai <= 3400) {
    Serial.println("AIR AGAK KERUH");
  } 
  else if (nilai <= 3700) {
    Serial.println("AIR CUKUP JERNIH");
  } 
  else {
    Serial.println("AIR SANGAT JERNIH");
  }
  
  delay(500);
}
