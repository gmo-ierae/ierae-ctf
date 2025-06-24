.section .text.boot
.global _start

_start:
    ldr sp, =0x08000000
    bl main
    
halt:
    b halt