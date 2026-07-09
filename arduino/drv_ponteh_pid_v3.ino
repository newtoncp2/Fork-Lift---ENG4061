#define ENCODER_OPTIMIZE_INTERRUPTS
#include <Encoder.h>
#include <Adafruit_INA219.h>
#include <ArduinoJson.h>

#define IN1 52
#define IN2 50
#define IN3 48
#define IN4 42
#define ENA 46
#define ENB 44

#define DIR 45
#define RS 49
#define EN 51
#define STP 47
#define FLT 53

#define B1 31
#define B2 35

#define KU 8
#define TU 0.125  // em s

#define KP (0.7 * KU)
#define KI 0 //(0.2*KU/TU) //(1.2 * KU / TU)
#define KD 0 //(0.04 * KU * TU)

#define KV (0.4 / 0.8)  // v_desejada / rho_tipico => setpoint de vel linear do robô e distância típica de detecção, algo entre 0.5m e 1m talvez? AJUSTAR
#define KW (5 * KV)     // normalmente entre 2KV e 3KV AJUSTAR

#define Ts 20

#define PI 3.1415926535897932384626433832795

Encoder encoderD(2, 3);
Encoder encoderE(19, 18);

Adafruit_INA219 INA;

const int DELAY_US = 200;
const int KS = 122;  // "ganho de step" : servidor envia 0 - 100 , motor gira 12200 passos da base ao topo

bool girar = false;
bool no_topo = false;
int passos_a_girar = 0;
int passos_girados = 0;

unsigned long instanteAnterior = 0;
unsigned long instanteAnterior2 = 0;

int modo = 0;

float rho = 0;
float theta = 0;
int pulsos = 0;

const float L = 0.195;                      // distância entre o meio das rodas em m (medido: 0.1722 m , melhor correção : )
const float R = 0.027;                      // raio da roda em m (medido: 0.02823 m , melhor correção : 0.027 m)
const float rpm_max = 150;                  // em rpm (obviamente??)
const float v_max = rpm_max * PI * R / 30;  // em m/s
const float w_max = 2 * v_max / L;
 
float rpm_e_temp, rpm_d_temp, v, w;

long inicial_e_auto = 0;
long inicial_d_auto = 0;

long atual_e = 0;
long atual_d = 0;

long inicial_e = 0;
long inicial_d = 0;

float rpm_desired_e = 0;
float rpm_desired_d = 0;

float rpm_e = 0;
float rpm_d = 0;

float error_e = 0;
float error_e_ant = 0;
float error_d = 0;
float error_d_ant = 0;

float prop_e = 0;
float int_e = 0;
float der_e = 0;
float prop_d = 0;
float int_d = 0;
float der_d = 0;

void enviarTelemetria(float tensao, float corrente, float potencia, bool falha_motor_passo, int rpm_e, int rpm_d) {
  JsonDocument msg;
  msg["tipo"] = "m";
  msg["falha_motor_passo"] = falha_motor_passo;
  msg["tensao_V"] = tensao;
  msg["corrente_mA"] = corrente;
  msg["potencia_mW"] = potencia;
  msg["rpm_esq"] = rpm_e;
  msg["rpm_dir"] = rpm_d;
  msg["t_ms"] = millis();

  serializeJson(msg, Serial);
}

void move_garfo() {
  digitalWrite(STP, HIGH);
  delayMicroseconds(DELAY_US);
  digitalWrite(STP, LOW);
  delayMicroseconds(DELAY_US);
}

void configura_ponteH(int motor_e, int motor_d) {
  if (motor_e <= 0) {
    digitalWrite(IN4, HIGH);
    digitalWrite(IN3, LOW);
  } else {
    digitalWrite(IN4, LOW);
    digitalWrite(IN3, HIGH);
  }

  if (motor_d <= 0) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
  } else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, HIGH);
  }
}

void move_robo_PID() {
  float saida_e = KP * prop_e + KI * int_e + KD * der_e;
  saida_e = constrain(saida_e, -255, 255);

  float saida_d = KP * prop_d + KI * int_d + KD * der_d;
  saida_d = constrain(saida_d, -255, 255);
  
  configura_ponteH(saida_e, saida_d);

  analogWrite(ENA, abs(saida_d));
  analogWrite(ENB, abs(saida_e));

  //Serial.print("saida_e:"); Serial.print(String(rpm_e)); Serial.print(","); Serial.print("saida_d:"); Serial.print(String(rpm_d)); Serial.print(","); Serial.print("fixo:"); Serial.println(200);
  //analogWrite(ENA, abs(rpm_desired_d)); analogWrite(ENB, abs(rpm_desired_e));  //modo sem PID
}

void procura_apriltag() {
  Serial.println("NAO ME IGNORE ME IMPLEMENTE POR FAVOR ME IMPLEMENTE :(");
}

void setup() {
  Serial.begin(115200);

  // pinos de alimentação de sensores
  pinMode(40, OUTPUT);
  pinMode(36, OUTPUT);
  pinMode(17, OUTPUT);
  pinMode(16, OUTPUT);
  pinMode(15, OUTPUT);
  pinMode(14, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(4, OUTPUT);

  digitalWrite(40, HIGH);
  digitalWrite(17, HIGH);
  digitalWrite(14, HIGH);
  digitalWrite(4, HIGH);

  digitalWrite(36, LOW);
  digitalWrite(16, LOW);
  digitalWrite(15, LOW);
  digitalWrite(5, LOW);

  //pinos do DRV
  digitalWrite(EN, LOW);   // ativo-baixo, LOW = habilitado
  digitalWrite(RS, HIGH);  // RST e SLP ativo-baixo
  digitalWrite(DIR, LOW);  // LOW = sobe
                           // M0 M1 M2 = 0 0 0 (flutuando) := modo full step (atualmente, M2 em curto com RS então modo 1/16)

  pinMode(EN, OUTPUT);
  pinMode(RS, OUTPUT);
  pinMode(DIR, OUTPUT);
  pinMode(STP, OUTPUT);
  pinMode(FLT, INPUT_PULLUP);  // quando digitalRead(FLT) = LOW, DRV sinalizou falha no motor

  //controle da ponteH
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);

  //fim de curso
  pinMode(B1, OUTPUT);
  pinMode(B2, INPUT_PULLUP);
  digitalWrite(B1, LOW);

  Wire.begin();
  if (!INA.begin()) {
    //Serial.println("Could not connect. Fix and Reboot");
  }

  INA.setCalibration_32V_2A();
}

void loop() {
  if (!digitalRead(FLT)) {
    analogWrite(ENA, 0);
    analogWrite(ENB, 0);

    digitalWrite(EN, HIGH);
  } else {
    if (Serial.available()) {
      String input = Serial.readStringUntil('\n');
      Serial.println("Recebi: " + input);

      modo = input.substring(0, 1).toInt();
      int i = input.indexOf(',');

      // se der bom, mover encoder.write(0) e atual = 0 pra cá, se der ruim, remover
            
      switch (modo) {
        case 0:  // modo manual
          encoderE.write(0);
          encoderD.write(0);
          atual_e = 0;
          atual_d = 0;
          rpm_e_temp = input.substring(2, i).toFloat();
          rpm_d_temp = input.substring(i + 1).toFloat();
          break;
        case 1:  // modo autônomo - giro no mesmo eixo
          encoderE.write(0);
          encoderD.write(0);
          atual_e = 0;
          atual_d = 0;
          theta = input.substring(2, i).toFloat();
          theta = constrain(theta, -2*PI, 2*PI);
          if (abs(theta) < 0.2) {theta = 0; int_e = 0; int_d = 0;}; // evita PWM ultra fraco e contagem inalcançável de pulsos

          pulsos = (abs(theta) * 720.0 * L) / (4 * PI * R);

          w = constrain(KW * theta, -w_max, w_max);
          
          rpm_e_temp = -(w * L / 2) * 30 / (PI * R); // - : angulo positivo = giro pra esquerda
          rpm_d_temp = (w * L / 2) * 30 / (PI * R);  // - : angulo positivo = giro pra direita

          break;
        case 2:  // modo autônomo - andar pra frente
          encoderE.write(0);
          encoderD.write(0);
          atual_e = 0;
          atual_d = 0;
          rho = input.substring(2, i).toFloat();
          rho = constrain(rho, -2, 2);

          if (abs(rho) < 0.03) {rho = 0; int_e = 0; int_d = 0;}; // evita PWM ultra fraco e contagem inalcançável de pulsos

          pulsos = (abs(rho) * 720.0) / (4 * PI * R);

          inicial_e_auto = 0;
          inicial_d_auto = 0;

          v = constrain(KV * rho, -v_max, v_max);

          rpm_e_temp = v * 30 / (PI * R);
          rpm_d_temp = v * 30 / (PI * R);

          break;
        case 3:  // modo de controle do garfo ()
          girar = true;
          passos_girados = 0;
          passos_a_girar = constrain(input.substring(2).toInt(), -100, 100) * KS;
  
          if (passos_a_girar <= 0) {
            digitalWrite(DIR, HIGH);
            passos_a_girar *= -1;
          } else {
            digitalWrite(DIR, LOW);
          }
          break;

        default:
          break;
      }

      rpm_desired_e = (float)constrain(rpm_e_temp, -rpm_max, rpm_max);
      rpm_desired_d = (float)constrain(rpm_d_temp, -rpm_max, rpm_max);
      //Serial.println("RPM_E: " + String(rpm_desired_e) + ", RPM_D: " + String(rpm_desired_d));
    }

    if (girar){
        if (passos_a_girar == passos_girados) {
          passos_a_girar = 0;
          passos_girados = 0;
          Serial.println("fim modo 3");
          modo = 0;
          girar = false;
      } else {
        no_topo = digitalRead(B2);
        
        if (!no_topo || (no_topo && digitalRead(DIR))) {
          move_garfo();
          passos_girados++;
        } else {
          passos_girados = passos_a_girar;
        }
      }
    }
    
    unsigned long instanteAtual = millis();
    if (instanteAtual - instanteAnterior > Ts) {
      double dt = (instanteAtual - instanteAnterior) / 1000.0f;
      instanteAnterior = instanteAtual;

      atual_d = encoderD.read();

      long dif_d = atual_d - inicial_d;
      rpm_d = (float)dif_d * 6000.0f / (72.0f * dt * 1000.0f);

      atual_e = encoderE.read();

      long dif_e = atual_e - inicial_e;
      rpm_e = (float)dif_e * 6000.0f / (72.0f * dt * 1000.0f);

      inicial_e = atual_e;
      inicial_d = atual_d;

      error_e = rpm_desired_e - rpm_e;
      prop_e = error_e;
      int_e += abs(error_e) < 40 ? error_e * dt : 0;
      der_e = (error_e - error_e_ant) / dt;

      error_d = rpm_desired_d - rpm_d;
      prop_d = error_d;
      int_d += abs(error_d) < 40 ? error_d * dt : 0;
      der_d = (error_d - error_d_ant) / dt;

      error_e_ant = error_e;
      error_d_ant = error_d;

      //Serial.println("enc_e: " + String(atual_e) + " " + "enc_d: " + String(atual_d));
      move_robo_PID();
    }

    if (abs(atual_e) > pulsos && abs(atual_d) > pulsos && (modo == 1 || modo == 2)) {
      pulsos = 0;
      rpm_desired_d = 0;
      rpm_d_temp = 0;
      rpm_desired_e = 0;
      rpm_e_temp = 0;
      Serial.println("fim modo " + String(modo));

      modo = 0;
    }

    if (millis() - instanteAnterior2 > 1500) {
      if (INA.getBusVoltage_V() < 9.7){
        Serial.println("comando de shutdown");
      }
      //enviarTelemetria(INA.getBusVoltage_V(), INA.getCurrent_mA(), INA.getPower_mW(), !digitalRead(FLT), rpm_e, rpm_d);
      instanteAnterior2 = millis();
    }
  }
}