"""PRNboard Rev A draft circuit. Pin maps from KiCad 10 libraries/manufacturer data.
This is engineering source, not a fabrication release. Python: conda base.
"""
from pathlib import Path
import os, json
import sexpdata as sx
ROOT=Path(__file__).resolve().parents[1]
LIB=Path(os.environ.get('KICAD_SYMBOL_DIR','/Volumes/KiCad/KiCad/KiCad.app/Contents/SharedSupport/symbols'))
parts=[]
def nodes(v,key):return [a for a in v if isinstance(a,list) and a and str(a[0])==key]
def symbol(lib,name):
 d=sx.load(open(LIB/(lib+'.kicad_sym'))); db={a[1]:a for a in nodes(d,'symbol')}
 def expand(n):
  v=db[n]; base=expand(nodes(v,'extends')[0][1]) if nodes(v,'extends') else []
  return base+[p for u in nodes(v,'symbol') for p in nodes(u,'pin')]
 pins=[]
 for p in expand(name):pins.append(dict(n=str(nodes(p,'number')[0][1]),label=str(nodes(p,'name')[0][1]),type=str(p[1])))
 props={a[1]:a[2] for a in nodes(db[name],'property')}
 return pins,props

def add(ref,value,section,x,y,lib=None,sym=None,nets=None,fp=None,mpn=None,cost=0.,lcsc=None,pins=None,rot=0,note=''):
 props={}
 if lib:pins,props=symbol(lib,sym)
 if isinstance(pins,list) and pins and isinstance(pins[0],str):pins=[dict(n=str(i+1),label=v,type='passive') for i,v in enumerate(pins)]
 nets=nets or {}
 for p in pins:p['net']=nets.get(p['n'])
 part=dict(ref=ref,value=value,section=section,x=x,y=y,rot=rot,pins=pins,footprint=fp or props.get('Footprint',''),mpn=mpn or value,cost_usd=cost,lcsc=lcsc,note=note)
 assert part['footprint'],ref
 parts.append(part);return part

def passive(ref,val,a,b,x,y,section='Power',kind='R',cost=.02,mpn=None):
 fp={'R':'Resistor_SMD:R_0603_1608Metric','C':'Capacitor_SMD:C_0603_1608Metric','L':'Inductor_SMD:L_0805_2012Metric'}[kind]
 return add(ref,val,section,x,y,nets={'1':a,'2':b},fp=fp,mpn=mpn or 'SELECT_IN_BOM',pins=['1','2'],cost=cost)
def cap(ref,net,x,y,section='Power',value='100n'):return passive(ref,value,net,'GND',x,y,section,'C')
# Regulator blocks: ESP radio current peaks isolated from GNSS/clock/DDS rails.
for ref,rail,x,y,enable in [('U1','3V3D',18,22,'USB5'),('U2','3V3RF',64,24,'USB5'),('U3','3V3G',78,25,'USB5')]:
 add(ref,'AP2112K-3.3', 'Power',x,y,pins=['VIN','GND','EN','NC','VOUT'],nets={'1':'USB5','2':'GND','3':enable,'5':rail},fp='Package_TO_SOT_SMD:SOT-23-5',mpn='AP2112K-3.3TRG1',cost=.18,lcsc='C51118')
for i,(rail,x,y) in enumerate([('USB5',14,22),('3V3D',22,22),('USB5',60,24),('3V3RF',68,24),('USB5',74,25),('3V3G',82,25)],1):cap('C'+str(i),rail,x,y,value='4u7')
# USB-C receptacle, both CC pull-downs. Connector pad map must be confirmed with exact supplier drawing.
add('J1','USB-C','Controller',12,7,pins=[dict(n=n,label=n,type='passive') for n in ['A1','A4','A5','A6','A7','A8','A9','A12','B1','B4','B5','B6','B7','B8','B9','B12','SH']],nets={**{n:'GND' for n in ['A1','A12','B1','B12','SH']},**{n:'USB5' for n in ['A4','A9','B4','B9']},'A5':'CC1','B5':'CC2','A6':'USB_DP','B6':'USB_DP','A7':'USB_DM','B7':'USB_DM'},fp='Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12',mpn='TYPE-C-31-M-12',cost=.35,lcsc='C165948')
passive('R1','5k1','CC1','GND',8,15,'Controller');passive('R2','5k1','CC2','GND',12,15,'Controller')
passive('R3','27','USB_DM','RP_DM',17,15,'Controller');passive('R4','27','USB_DP','RP_DP',20,15,'Controller')
# RP2040 remains on its own 12MHz crystal for normal ROM USB recovery.
rp={n:'3V3D' for n in ['1','10','22','33','42','43','44','48','49']}
rp.update({n:'1V1' for n in ['23','45','50']});rp.update({'57':'GND','19':'GND','20':'XIN','21':'XOUT','24':'SWCLK','25':'SWDIO','26':'RUN','46':'RP_DM','47':'RP_DP','51':'QSPI3','52':'QSPI_CLK','53':'QSPI0','54':'QSPI2','55':'QSPI1','56':'QSPI_CS'})
# Physical pin numbers checked against RP2040 datasheet. UART0 Wi-Fi, UART1 GNSS.
gpio={0:'WIFI_RX',1:'WIFI_TX',2:'I2C_SDA',3:'I2C_SCL',4:'GNSS_RX',5:'GNSS_TX',6:'PPS',7:'REF10',8:'DDS_DATA',9:'DDS_WCLK',10:'DDS_UPDATE',11:'DDS_RESET',12:'TX_REQUEST',13:'QUALIFIED',14:'HEARTBEAT',15:'PPS_ALIVE',16:'WD_ALIVE',17:'PA_OK',18:'GPIO0',19:'GPIO1',20:'DDS_PS0',21:'DDS_SYNC_CLK',22:'TX_ENABLE',23:'WIFI_EN',24:'WIFI_BOOT',25:'STATUS_LED',26:'ADC_PA_FWD',27:'ADC_PA_REV',28:'DDS_CS_N',29:'DDS_SDO'}
for p in symbol('MCU_RaspberryPi','RP2040')[0]:
 if p['label'].startswith('GPIO'):
  n=int(p['label'][4:].split('/')[0]);rp[p['n']]=gpio.get(n)
add('U4','RP2040','Controller',28,34,'MCU_RaspberryPi','RP2040',rp,mpn='RP2040',cost=.9,lcsc='C2040')
add('U5','W25Q16JVSS','Controller',16,35,'Memory_Flash','W25Q16JVSS',{'1':'QSPI_CS','2':'QSPI1','3':'QSPI2','4':'GND','5':'QSPI0','6':'QSPI_CLK','7':'QSPI3','8':'3V3D'},cost=.35)
passive('R5','10k','QSPI_CS','3V3D',16,30,'Controller');passive('R6','10k','RUN','3V3D',25,24,'Controller')
add('Y1','12MHz','Controller',28,46,pins=['X1','GND','X2','GND'],nets={'1':'XIN','2':'GND','3':'XTAL_OUT','4':'GND'},fp='Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm',mpn='ABM8-272-T3',cost=.2)
passive('R7','1k','XTAL_OUT','XOUT',32,46,'Controller');cap('C7','XIN',24,46,'Controller','15p');cap('C8','XTAL_OUT',28,50,'Controller','15p')
for i,(rail,x,y) in enumerate([('3V3D',25,29),('3V3D',31,29),('3V3D',33,34),('3V3D',31,39),('3V3D',25,39),('1V1',23,34),('1V1',29,41),('3V3D',16,39)],9):cap('C'+str(i),rail,x,y,'Controller')
cap('C17','1V1',23,38,'Controller','1u');cap('C18','RUN',25,21,'Controller')
# ESP module antenna extends beyond north edge. No copper/component/metal under antenna.
esp={'1':'GND','2':'3V3D','3':'WIFI_EN','27':'WIFI_BOOT','36':'WIFI_RX','37':'WIFI_TX','40':'GND','41':'GND'}
add('U6','ESP32-S3-WROOM-1-N8','Wi-Fi',49,9,'RF_Module','ESP32-S3-WROOM-1',esp,mpn='ESP32-S3-WROOM-1-N8',cost=4.216,lcsc='C2913198',note='Standard PCBA only on checked JLC page. Keep antenna clear on every layer.')
cap('C19','3V3D',38,21,'Wi-Fi','10u');cap('C20','3V3D',41,21,'Wi-Fi');cap('C21','WIFI_EN',44,24,'Wi-Fi')
passive('R8','10k','WIFI_EN','3V3D',40,24,'Wi-Fi');passive('R9','10k','WIFI_BOOT','3V3D',44,28,'Wi-Fi')
# Single-frequency fallback permitted by user; external raw/dual frequency receiver header later.
g={'1':'GND','2':'GNSS_TX','3':'GNSS_RX','4':'PPS','6':'3V3G','7':'3V3G','8':'3V3G','10':'GND','11':'GNSS_RF','12':'GND'}
add('U7','MAX-M10S-00B','GNSS',78,12,'RF_GPS','MAX-M10S',g,mpn='MAX-M10S-00B',cost=10.5062,lcsc='C4153167',note='VIO_SEL and TIMEPULSE/SAFEBOOT left unpulled. Single-frequency: no dual-frequency TEC.')
cap('C22','3V3G',70,12,'GNSS');cap('C23','3V3G',70,16,'GNSS','4u7')
add('J2','GNSS ANT','GNSS',88,12,pins=['RF','GND'],nets={'1':'ANT_RF','2':'GND'},fp='Connector_Coaxial:SMA_Amphenol_132134_Vertical',mpn='132134',cost=1.5,note='Candidate vertical SMA; supplier/price not frozen.')
passive('C24','100p','ANT_RF','GNSS_RF',83,12,'GNSS','C');passive('L1','27n','ANT_BIAS','ANT_RF',86,18,'GNSS','L',.12);passive('R10','100','3V3G','ANT_BIAS',82,21,'GNSS',cost=.03);cap('C25','ANT_BIAS',86,23,'GNSS','1n')
# Antenna supply current limited by 100ohm/0.25W resistor: check antenna headroom.
parts[-2]['note']='Use >=0.25W 0805 and check active-antenna voltage/current; provisional bias network.'
parts[-2]['footprint']='Resistor_SMD:R_0805_2012Metric'
# Servo DAC and VCTCXO, clipped sine reshaped by fast comparator.
add('U8','MCP4725A1T-E/CH','Reference',45,38,'Analog_DAC','MCP4725xxx-xCH',{'1':'DAC','2':'GND','3':'3V3RF','4':'I2C_SDA','5':'I2C_SCL','6':'GND'},cost=1.1,lcsc='C61423')
passive('R11','1k','DAC','DAC_FILTER',50,38,'Reference');passive('R12','1k','DAC_FILTER','VCTRL',55,38,'Reference');cap('C26','DAC_FILTER',50,42,'Reference','4u7');cap('C27','VCTRL',55,42,'Reference','4u7')
add('Y2','10MHz VCTCXO','Reference',61,38,pins=['VC','GND','OUT','VCC'],nets={'1':'VCTRL','2':'GND','3':'OSC_SINE','4':'3V3RF'},fp='Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm',mpn='1XTV10000MDA',cost=1.1,lcsc='C253701',note='KDS drawing/underbody copper keepout needs custom footprint review before routing.')
cap('C28','3V3RF',61,34,'Reference');passive('C29','1n','OSC_SINE','SINE_AC',66,38,'Reference','C');passive('R13','10k','3V3RF','MID',66,32,'Reference');passive('R14','10k','MID','GND',70,32,'Reference');cap('C30','MID',70,35,'Reference','4u7');passive('R15','10k','MID','SINE_AC',70,39,'Reference')
add('U9','TLV3501AIDBVR','Reference',75,38,pins=['IN-','GND','IN+','VCC','OUT','SHDN'],nets={'1':'MID','2':'GND','3':'SINE_AC','4':'3V3RF','5':'REF10','6':'GND'},fp='Package_TO_SOT_SMD:SOT-23-6',cost=2.2)
cap('C31','3V3RF',77,34,'Reference');cap('C32','3V3RF',45,34,'Reference')
passive('R16','1k','I2C_SDA','3V3D',38,32,'Reference');passive('R17','1k','I2C_SCL','3V3D',38,35,'Reference')
# AD9954 uses its own x20 PLL: 10 MHz disciplined reference -> 200 MHz DDS.
# Separate analog/digital 1.8V regulators follow manufacturer supply guidance.
for ref,rail,x,y in [('U10','1V8A',72,47),('U17','1V8D',47,47)]:
 add(ref,'AP2112K-1.8','Power',x,y,pins=[dict(n=str(i+1),label=n,type=t) for i,(n,t) in enumerate([('VIN','power_in'),('GND','power_in'),('EN','input'),('NC','no_connect'),('VOUT','power_out')])],nets={'1':'3V3RF','2':'GND','3':'3V3RF','5':rail},fp='Package_TO_SOT_SMD:SOT-23-5',mpn='AP2112K-1.8TRG1',cost=.20,note='Input from regulated 3V3RF; check rail sequencing and decoupling.')
cap('C33','3V3RF',69,44,'Power','4u7');cap('C34','1V8A',75,47,'Power','4u7')
cap('C35','3V3RF',44,47,'Power','4u7');cap('C36','1V8D',50,47,'Power','4u7')
# Reference swing must be 100..1000mVpp, not 3.3V CMOS. Divider precedes AC coupling.
passive('R18','330','REF10','REF_ATT',72,43,'Reference')
passive('R19','100','REF_ATT','GND',76,43,'Reference')
passive('C37','100n','REF_ATT','DDS_REF',66,47,'Reference','C')
passive('C54','100n','REF_N','1V8A',64,43,'DDS','C')
# x20 PLL external loop compensation per AD9954 datasheet Table4:243ohm +10nF.
passive('R20','243','DDS_PLL','PLL_RC',54,44,'DDS');cap('C55','PLL_RC',57,44,'DDS','10n')
dds={'1':'DDS_UPDATE','2':'1V8D','3':'GND','4':'1V8A','5':'GND','6':'1V8A','7':'GND','8':'REF_N','9':'DDS_REF','11':'GND','12':'DDS_PLL','13':'1V8A','14':'GND','15':'GND','16':'1V8A','17':'GND','18':'1V8A','19':'1V8A','20':'DAC_B','21':'DAC_A','22':'GND','23':'DAC_BP','24':'RSET','25':'1V8A','26':'GND','27':'1V8A','29':'1V8A','30':'GND','31':'GND','32':'GND','33':'GND','34':'1V8D','35':'GND','36':'DDS_RESET','37':'GND','38':'DDS_SDO','39':'DDS_CS_N','40':'DDS_WCLK','41':'DDS_DATA','42':'GND','43':'3V3D','44':'GND','45':'DDS_SYNC_CLK','46':'GND','47':'DDS_PS0','48':'GND','49':'GND'}
add('U11','AD9954YSVZ-REEL7','DDS',58,55,'Interface','AD9954',dds,mpn='AD9954YSVZ-REEL7',cost=45.1932,lcsc='C496484',note='14-bit DAC; autonomous LFM; x20 PLL200MHz. Core1.8V, IO3.3V. DAC returns to AVDD, not ground.')
passive('R21','3k92','RSET','GND',51,49,'DDS')
passive('R22','49R9','DAC_B','1V8A',51,59,'DDS');passive('R23','49R9','DAC_A','1V8A',65,59,'DDS')
for i,(rail,x,y) in enumerate([('1V8A',53,51),('1V8A',53,54),('1V8A',53,57),('1V8A',58,49),('1V8A',62,49),('1V8A',63,52),('1V8A',63,55),('1V8A',62,60),('1V8A',58,61),('1V8D',53,61),('1V8D',58,64),('3V3D',63,62)],56):cap('C'+str(i),rail,x,y,'DDS')
cap('C38','DAC_BP',54,63,'DDS')
passive('R39','10k','DDS_CS_N','3V3D',43,51,'DDS');passive('R40','10k','DDS_PS0','GND',43,55,'DDS')
# Correct library electrical types against manufacturer pin table, including SYNC_IN.
for pin in next(p for p in parts if p['ref']=='U11')['pins']:
 if pin['n'] in ['1','44']:pin['type']='input'
# Seven-pole Butterworth 35MHz reconstruction, nominal matched 50ohm source and load.
for i,(val,a,b,x) in enumerate([('100n','DAC_A','LP1',65),('390n','LP1','LP2',71),('390n','LP2','LP3',77),('100n','LP3','LP_OUT',83)],2):passive('L'+str(i),val,a,b,x,59,'RF','L',.12)
for i,(val,net,x) in enumerate([('110p','LP1',68),('180p','LP2',74),('110p','LP3',80)],42):cap('C'+str(i),net,x,63,'RF',val)
passive('R24','49R9','LP_OUT','1V8A',86,59,'RF');passive('C45','100n','LP_OUT','RF_IN_AC',87,63,'RF','C')
passive('R25','10k','RF_IN_AC','MID',87,67,'RF')
# SPDT mute before driver, mute selects DC bias. Exact switch truth table must be checked before release.
add('U12','TS5A3159DBVR','RF',81,70,'Analog_Switch','TS5A3159DBV',{'1':'RF_IN_AC','2':'GND','3':'AMP_IN','4':'MID','5':'3V3RF','6':'TX_ENABLE'},mpn='TS5A3159DBVR',cost=.5,note='Pin1 NO, pin3 COM, pin4 NC: high enables RF; low selects MID.')
add('U13','OPA356AIDBVR','RF',72,71,'Amplifier_Operational','OPA356xxDBV',{'1':'AMP_OUT','2':'GND','3':'AMP_IN','4':'AMP_FB','5':'3V3RF'},mpn='OPA356AIDBVR',cost=1.8)
passive('R26','300','AMP_OUT','AMP_FB',72,67,'RF');passive('R27','100','AMP_FB','MID',68,67,'RF');passive('R28','49R9','AMP_OUT','RF_SERIES',67,71,'RF');passive('C46','100n','RF_SERIES','RF_OUT',62,71,'RF','C')
cap('C47','3V3RF',75,75,'RF');cap('C48','3V3RF',83,74,'RF')
add('J3','EXCITER OUT','RF',55,76,pins=['RF','GND'],nets={'1':'RF_OUT','2':'GND'},fp='Connector_Coaxial:SMA_Amphenol_132134_Vertical',mpn='132134',cost=1.5)
# Missing PPS and firmware heartbeat: independent retriggerable monostables.
wd={'1':'GND','2':'PPS','3':'RUN','4':None,'5':'WD_ALIVE','6':'WD_C','7':'WD_RC','8':'GND','9':'GND','10':'HEARTBEAT','11':'RUN','12':None,'13':'PPS_ALIVE','14':'PPS_C','15':'PPS_RC','16':'3V3D'}
add('U14','74HC123D','Interlock',28,63,'74xx','74HC123',wd,fp='Package_SO:SOIC-16_3.9x9.9mm_P1.27mm',mpn='74HC123D,653',cost=.3)
passive('R29','1M','3V3D','PPS_RC',22,56,'Interlock');passive('C49','4u7','PPS_C','PPS_RC',25,56,'Interlock','C')
passive('R30','100k','3V3D','WD_RC',22,70,'Interlock');passive('C50','1u','WD_C','WD_RC',25,70,'Interlock','C');cap('C51','3V3D',32,57,'Interlock')
add('U15','74LVC2G08','Interlock',39,63,'74xGxx','74LVC2G08',{'1':'PPS_ALIVE','2':'WD_ALIVE','7':'CLOCK_ALIVE','3':'ARMED','5':'QUALIFIED','6':'TX_REQUEST','4':'GND','8':'3V3D'},fp='Package_SO:VSSOP-8_2.3x2mm_P0.5mm',mpn='74LVC2G08DC,125',cost=.15)
add('U16','SN74LVC1G08DBVR','Interlock',44,69,pins=['A','B','GND','Y','VCC'],nets={'1':'CLOCK_ALIVE','2':'ARMED','3':'GND','4':'TX_ENABLE','5':'3V3D'},fp='Package_TO_SOT_SMD:SOT-23-5',cost=.12)
for i,(net,x,y) in enumerate([('TX_REQUEST',35,56),('QUALIFIED',38,56),('HEARTBEAT',41,56),('TX_ENABLE',47,69)],31):passive('R'+str(i),'10k',net,'GND',x,y,'Interlock')
cap('C52','3V3D',39,59,'Interlock');cap('C53','3V3D',44,65,'Interlock')
# Headers: no PA supply or 10W circuitry on this board.
for ref,name,nets,x,y in [('J4','SWD',['GND','3V3D','SWCLK','SWDIO','RUN'],9,37),('J5','ESP PROGRAM',['GND','3V3D','WIFI_RX','WIFI_TX','WIFI_EN','WIFI_BOOT'],9,52),('J6','GNSS EXPANSION',['GND','3V3G','GNSS_RX','GNSS_TX','PPS','REF10'],88,38),('J7','PA CONTROL',['GND','TX_ENABLE','PA_OK','ADC_PA_FWD','ADC_PA_REV','GND'],11,72),('J8','DIGITAL IO',['GND','3V3D','GPIO0','GPIO1'],44,76)]:
 add(ref,name,'Expansion',x,y,pins=[str(i+1) for i in range(len(nets))],nets={str(i+1):v for i,v in enumerate(nets)},fp=f'Connector_PinHeader_2.54mm:PinHeader_1x{len(nets):02d}_P2.54mm_Vertical',cost=.15,note='3.3V logic only. External GNSS must replace onboard UART/PPS source; never parallel output drivers.')
passive('R35','10k','PA_OK','GND',16,67,'Interlock')
# Status LED and debug boot contacts are not relied upon for safety.
add('D1','GREEN','Controller',34,22,pins=['K','A'],nets={'1':'GND','2':'LED_A'},fp='LED_SMD:LED_0603_1608Metric',cost=.03);passive('R36','1k','STATUS_LED','LED_A',34,25,'Controller')
for ref,net,x,y in [('SW1','RUN',7,28),('SW2','QSPI_CS',7,22)]:
 add(ref,'RESET' if ref=='SW1' else 'BOOT','Controller',x,y,pins=['1','2'],nets={'1':net,'2':'GND'},fp='Button_Switch_SMD:SW_SPST_TL3342',mpn='TL3342F160QG',cost=.1)
# ESD protection and isolatable onboard GNSS outputs for a later TEC receiver.
add('D2','USBLC6-2SC6','Controller',16,11,pins=['IO1','GND','IO2','IO2','VBUS','IO1'],nets={'1':'USB_DM','2':'GND','3':'USB_DP','4':'USB_DP','5':'USB5','6':'USB_DM'},fp='Package_TO_SOT_SMD:SOT-23-6',cost=.2,lcsc='C7519')
next(p for p in parts if p['ref']=='U7')['pins'][1]['net']='GNSS_TX_ONBOARD'
next(p for p in parts if p['ref']=='U7')['pins'][3]['net']='PPS_ONBOARD'
passive('R37','0','GNSS_TX_ONBOARD','GNSS_TX',72,20,'GNSS')
passive('R38','0','PPS_ONBOARD','PPS',75,20,'GNSS')
for p in parts:
 if p['ref'] in ['U1','U2','U3']:
  for pin in p['pins']:pin['type']={'1':'power_in','2':'power_in','3':'input','4':'no_connect','5':'power_out'}[pin['n']]
 if p['ref']=='J1':
  for pin in p['pins']:
   if pin['n'] in ['A1','A4']:pin['type']='power_out'
 if p['ref']=='J7':p['y']=65

for p in parts:
 if p['ref']=='U9':
  for pin in p['pins']:pin['type']={'1':'input','2':'power_in','3':'input','4':'power_in','5':'output','6':'input'}[pin['n']]
 if p['ref']=='U16':
  for pin in p['pins']:pin['type']={'1':'input','2':'input','3':'power_in','4':'output','5':'power_in'}[pin['n']]
# Produce JSON, not CSV. Every cost is an estimate unless its source is in sourcing.json.
if __name__=='__main__':
 out=ROOT/'hardware';out.mkdir(exist_ok=True)
 d=dict(revision='B-draft',status='NOT_FOR_FABRICATION',width_mm=95,height_mm=85,parts=parts)
 (out/'circuit.json').write_text(json.dumps(d,indent=2)+'\n')
 print(len(parts),'components; estimated component subtotal $',round(sum(p['cost_usd'] for p in parts),2))
