#include <linux/errno.h>
#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/slab.h>

MODULE_AUTHOR("Rona");
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("free2free - Kernel Driver for Ierae CTF 2024");

#define CMD_ADD_OBJ 0x1000
#define CMD_DEL_OBJ 0x1001
#define CMD_SUPER_DEL_OBJ 0x1002
#define NUM_OBJ 3

struct mutex mtx;
struct object {
  void *ptr;
  bool is_alloced;
};
struct object objs[NUM_OBJ] = {0};
static bool did_super_del = false;

static long chal_ioctl(struct file *filp, unsigned int cmd, unsigned long arg) {
  long ret = -EINVAL;
  unsigned long idx;
  mutex_lock(&mtx);

  switch (cmd) {
    case CMD_ADD_OBJ:
      for (idx = 0; idx < NUM_OBJ; idx++) {
        if (objs[idx].ptr || objs[idx].is_alloced) continue;
        objs[idx].ptr = kmalloc(arg, GFP_KERNEL);
        objs[idx].is_alloced = true;
        ret = idx;
        break;
      }
      break;
    case CMD_DEL_OBJ:
      idx = arg;
      if (idx < NUM_OBJ && objs[idx].is_alloced) {
        kfree(objs[idx].ptr);
        objs[idx].is_alloced = false;
        ret = 0;
      }
      break;
    case CMD_SUPER_DEL_OBJ:
      idx = arg;
      if (!did_super_del && idx < NUM_OBJ) {
        kfree(objs[idx].ptr);
        did_super_del = true;
        memset(objs, '\0', sizeof(objs));
        ret = 0;
      }
      break;
  }

end:
  mutex_unlock(&mtx);
  return ret;
}

static const struct file_operations chal_fops = {
    .owner = THIS_MODULE,
    .unlocked_ioctl = chal_ioctl,
};

static struct miscdevice chal_device = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = "chal",
    .fops = &chal_fops,
};

static int __init chal_init(void) {
  mutex_init(&mtx);
  return misc_register(&chal_device);
}

static void __exit chal_exit(void) { misc_deregister(&chal_device); }

module_init(chal_init);
module_exit(chal_exit);
