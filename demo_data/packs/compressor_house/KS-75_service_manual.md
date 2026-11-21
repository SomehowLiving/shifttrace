<!-- FICTIONAL demo manual for the SHIFTTRACE hackathon prototype. Not a real product. Do not use for real equipment. -->
# Kestrel KS-75 Rotary Screw Air Compressor: Service Manual (excerpt)

## 1.2 Control panel indicators and alarm codes
The KS-75 panel has five lamps: RUN (green), LOAD (green), TEMP HIGH (amber, turns red and flashes at shutdown level), SERVICE (amber) and FAULT (red). The display shows the active alarm code, discharge temperature and drive-end vibration velocity.
Alarm A-17 DISCHARGE TEMP HIGH: warning at 105 °C, automatic shutdown at 115 °C. Alarm A-22 VIBRATION HIGH: warning at 7.1 mm/s RMS, shutdown at 11.0 mm/s RMS. Alarm A-31 OIL PRESSURE LOW. A warning lamp alone does not identify the root cause; follow the troubleshooting section for the code.

## 4.2 Troubleshooting A-17 discharge temperature high
Check causes in this order: (1) oil level low in separator tank; (2) oil cooler fins blocked or cooling fan not running; (3) thermostatic valve stuck; (4) discharge temperature sensor TS-2 faulty or loose connector; (5) ambient temperature above 46 °C or poor room ventilation.
If A-17 recurs after the sensor TS-2 has been replaced, the sensor is unlikely to be the cause. Excess friction from worn motor or airend bearings can raise discharge temperature; correlate with drive-end vibration readings (section 6.3). Record whether vibration rises before or after the temperature warning; this helps separate a cooling problem from a mechanical one.

## 6.3 Motor bearing vibration limits and inspection
Measure velocity RMS at the motor drive end (DE) and non-drive end (NDE) with the unit loaded. Zones: up to 2.8 mm/s good; 2.8 to 7.1 mm/s acceptable, monitor trend; 7.1 to 11.0 mm/s alarm, plan bearing replacement at the next opportunity; above 11.0 mm/s stop the unit.
Bearings: motor DE 6316-C3 (part BRG-6316-C3), motor NDE 6314-C3 (part BRG-6314-C3). A DE reading in the alarm zone with a normal NDE reading points to the DE bearing or to coupling misalignment (section 6.4). Bearing replacement requires lockout and tagout (section 7.1) and should be done by an authorised technician.

## 6.4 Coupling alignment and elastomer insert
Misalignment between motor and airend typically produces vibration at twice running speed and premature wear of the elastomer insert (part CPL-INS-90). Inspect the insert for cracking and check angular and parallel alignment with a dial gauge or laser tool. Tolerance: 0.05 mm parallel, 0.05 mm per 100 mm angular. Re-check alignment after any bearing replacement.

## 7.1 Lockout and tagout before mechanical work
Before any bearing, coupling or airend work: stop the unit from the panel, isolate the main breaker and apply a personal lock and tag, close the discharge isolation valve, and bleed residual pressure through the blowdown valve until the gauge reads zero. Verify zero energy by attempting a start. Never rely on the panel STOP button alone.

## 8.1 Lubrication schedule
Regrease motor bearings every 2,000 running hours with 25 g per bearing of EP2 lithium-complex grease (part GRS-EP2). Over-greasing raises bearing temperature. Replace the oil filter (FLT-OIL-75) every 4,000 hours.

## 8.2 Quarterly preventive maintenance checklist
Work through these steps in order and record each one: (1) apply lockout and tagout per section 7.1; (2) check separator tank oil level at the sight glass with the unit stopped, top up with KS synthetic oil if below the MIN mark; (3) replace the oil filter FLT-OIL-75 if it is due (every 4,000 hours); (4) regrease motor DE and NDE bearings, 25 g each of GRS-EP2; (5) clean the oil cooler fins with low-pressure air from the fan side; (6) inspect the coupling insert CPL-INS-90 for cracks (section 6.4); (7) drain the condensate trap and confirm it discharges; (8) remove locks, start the unit and record discharge temperature and DE and NDE vibration after 15 minutes loaded.

## 9.1 Shift inspection round readings and limits
Record these readings once per shift with the unit loaded: discharge temperature (normal 80 to 100 °C, warning 105 °C); DE vibration velocity (zones in section 6.3; above 7.1 mm/s is alarm); separator oil level (between MIN and MAX at the sight glass); discharge pressure (7.0 to 7.5 bar); condensate trap discharging every cycle; no oil leaks under the airend. Any reading outside its limit must be reported to the shift supervisor and logged against the asset.
