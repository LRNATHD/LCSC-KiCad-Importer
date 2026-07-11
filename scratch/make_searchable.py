import csv
import re
import sys

def extract_keywords(description, category, part_number):
    keywords = set()
    text = f"{description} {category} {part_number}".upper()
    
    # Value Extractors
    voltages = re.findall(r'(\d+(?:\.\d+)?\s*V)', text)
    currents = re.findall(r'(\d+(?:\.\d+)?\s*(?:MA|A|UA))', text)
    freqs = re.findall(r'(\d+(?:\.\d+)?\s*(?:MHZ|KHZ|HZ))', text)
    ohms = re.findall(r'(\d+(?:\.\d+)?\s*(?:K|M|M)?(?:OHM|Ω))', text)
    caps = re.findall(r'(\d+(?:\.\d+)?\s*(?:UF|NF|PF|F))', text)
    inds = re.findall(r'(\d+(?:\.\d+)?\s*(?:UH|NH|MH|H))', text)
    power = re.findall(r'(\d+(?:\.\d+)?(?:/\d+)?\s*W)', text)
    
    for v in voltages: keywords.add(v.replace(' ', ''))
    for c in currents: keywords.add(c.replace(' ', ''))
    for f in freqs: keywords.add(f.replace(' ', ''))
    for o in ohms: keywords.add(o.replace(' ', ''))
    for c in caps: keywords.add(c.replace(' ', ''))
    for i in inds: keywords.add(i.replace(' ', ''))
    for p in power: keywords.add(p.replace(' ', ''))

    # Categorical Keywords
    if 'REG' in text or 'LDO' in text:
        keywords.update(['Power', 'Voltage Regulator', 'Power Supply', 'LDO'])
    if 'MOSFET' in text or 'N-CH' in text or 'P-CH' in text:
        keywords.update(['Transistor', 'Switch', 'FET'])
    if 'DIODE' in text or 'RECTIFIER' in text or 'ZENER' in text or 'SCHOTTKY' in text:
        keywords.update(['Semiconductor', 'Rectifier', 'Diode'])
    if 'ANT' in text or 'ANTENNA' in text:
        keywords.update(['Antenna', 'Wireless', 'RF', 'Radio'])
    if 'CRYSTAL' in text or 'OSCILLATOR' in text or 'RESONATOR' in text:
        keywords.update(['Clock', 'Timing', 'Oscillator', 'Resonator'])
    if 'MTR DRVR' in text or 'MOTOR' in text or 'STEP/' in text:
        keywords.update(['Motor Driver', 'Actuator', 'Motion Control'])
    if 'AMP' in text or 'SPEAKER' in text or 'AUDIO' in text:
        keywords.update(['Audio', 'Sound', 'Acoustic'])
    if 'CONN' in text or 'USB' in text or 'HEADER' in text or 'SOCKET' in text:
        keywords.update(['Connector', 'Interconnect', 'Plug', 'Receptacle'])
    if 'SWITCH' in text or 'TACTILE' in text or 'PUSHBUTTON' in text:
        keywords.update(['Button', 'Input', 'Switch', 'Tactile'])
    if 'LED' in text:
        keywords.update(['Light', 'Indicator', 'Optoelectronics'])
    if 'WIFI' in text or 'BT' in text or 'BLUETOOTH' in text or 'RF TXRX' in text or 'ESP32' in text:
        keywords.update(['Wireless', 'Radio', 'Transceiver', 'IoT'])
    if 'MICROCONTROLLER' in text or 'MCU' in text or 'RISC-V' in text or '32 BIT' in text:
        keywords.update(['MCU', 'Microcontroller', 'Processor', 'Brain', 'Compute'])
    if 'CAP CER' in text or 'CAPACITOR' in text:
        keywords.update(['Capacitor', 'Passive', 'Energy Storage', 'Decoupling'])
    if 'RES ' in text or 'RESISTOR' in text:
        keywords.update(['Resistor', 'Passive', 'Impedance'])
    if 'IND ' in text or 'INDUCTOR' in text or 'CHOKE' in text or 'COIL' in text:
        keywords.update(['Inductor', 'Passive', 'Coil', 'Choke', 'Magnetic'])
    if 'BATTERY' in text or 'LITHIUM' in text or 'BMS' in text or 'MANAGEMENT ICS' in text or 'TP4057' in text:
        keywords.update(['Power', 'Energy', 'Battery Management', 'Charging'])

    # Generic
    if 'SMD' in text or 'SURFACE MOUNT' in text or 'SMT' in text:
        keywords.add('SMD')
    if 'THROUGH HOLE' in text or 'TH' in text:
        keywords.add('THT')

    return ", ".join(sorted(keywords))

def main():
    input_file = 'Consolidated_Parts.csv'
    output_file = 'Searchable_Parts.csv'
    
    with open(input_file, 'r', encoding='utf-8') as fin, open(output_file, 'w', encoding='utf-8', newline='') as fout:
        reader = csv.reader(fin)
        writer = csv.writer(fout)
        
        headers = next(reader)
        headers.append('Keywords (Search Tags)')
        writer.writerow(headers)
        
        # Determine column indices
        desc_idx = headers.index('Description') if 'Description' in headers else 6
        cat_idx = headers.index('Category/Package') if 'Category/Package' in headers else 7
        part_idx = headers.index('Manufacturer Part Number') if 'Manufacturer Part Number' in headers else 4
        
        for row in reader:
            if not any(row): continue # Skip empty rows
            
            desc = row[desc_idx] if len(row) > desc_idx else ''
            cat = row[cat_idx] if len(row) > cat_idx else ''
            part = row[part_idx] if len(row) > part_idx else ''
            
            kw = extract_keywords(desc, cat, part)
            
            # Append keywords to row
            new_row = list(row)
            new_row.append(kw)
            writer.writerow(new_row)

    print(f"Successfully generated {output_file} with enriched keywords.")

if __name__ == '__main__':
    main()
