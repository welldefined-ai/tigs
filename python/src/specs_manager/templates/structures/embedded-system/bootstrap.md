# /bootstrap - Generate Embedded System Specifications from Code

Generate initial specification structure for embedded systems by analyzing existing firmware, hardware definitions, and protocol implementations.

## Your Task

Analyze the codebase and generate specifications for embedded system components.

## Spec Types to Generate

Create specifications in these types based on what you find:

### hardware/
Hardware components, interfaces, and electrical specifications:
- Microcontroller/processor specifications
- Peripheral interfaces (GPIO, ADC, PWM, etc.)
- Communication buses (I2C, SPI, UART, CAN)
- Power supply requirements
- Pin configurations and mappings

### firmware/
Firmware modules and low-level software:
- Device drivers and HAL implementations
- Interrupt handlers and service routines
- Memory management and allocation
- RTOS tasks and scheduling
- Boot loader and startup code

### protocols/
Communication protocols and message formats:
- Serial communication protocols
- Network protocols (TCP/IP, UDP, MQTT, etc.)
- Custom protocol definitions
- Message structures and encoding
- Error handling and retries

### power-management/
Power states and energy optimization:
- Operating modes (active, sleep, deep sleep)
- Power consumption profiles
- Wake-up sources and triggers
- Clock management and frequency scaling
- Battery management strategies

## Analysis Steps

1. **Scan Hardware Definitions**
   - Look for pinout configurations, register definitions
   - Identify microcontroller model and peripherals
   - Extract hardware constraints and specifications

2. **Analyze Firmware Structure**
   - Identify main modules and their responsibilities
   - Map out driver implementations
   - Document interrupt handlers and ISRs
   - Catalog RTOS tasks if present

3. **Extract Protocol Information**
   - Find communication protocol implementations
   - Document message formats and structures
   - Identify protocol state machines
   - Note error handling strategies

4. **Document Power Management**
   - Identify power modes and transitions
   - Map wake-up sources
   - Document clock configurations
   - Note power-saving strategies

## Output Format

Generate one specification directory per major component/subsystem found, placed in the appropriate spec type directory.

Each spec should follow the embedded system specification format with:
- Component identification
- Technical requirements
- Interface definitions
- Operating constraints
- Test/validation criteria

## Important Notes

- Focus on the "what" and "why", not just the "how"
- Document hardware constraints and limitations
- Include timing requirements and real-time constraints
- Note safety-critical components
- Reference relevant datasheets and standards
