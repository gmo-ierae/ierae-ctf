ENTRY(_start)

SECTIONS
{
    . = 0x10000;  /* Start address for versatile-pb */
    
    .text : {
        *(.text.boot)
        *(.text)
    }
    
    .rodata : {
        *(.rodata)
    }
    
    .data : {
        *(.data)
    }
    
    . = ALIGN(4);
    __bss_start = .;
    .bss : {
        *(.bss)
        *(COMMON)
    }
    __bss_end = .;
    
    . = ALIGN(8);
    stack_top = .;

    . = 0x20000;
    .flag : {
        *(.flag)
    }
}
