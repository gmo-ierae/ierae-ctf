#include <linux/cdev.h>
#include <linux/device.h>
#include <linux/fs.h>
#include <linux/kernel.h>
#include <linux/list.h>
#include <linux/miscdevice.h>
#include <linux/module.h>
#include <linux/slab.h>
#include <linux/uaccess.h>

#define DEVICE_NAME "vibexec"
#define CACHE_NAME "vibexec_cache"

#define IOCTL_ADD_ITEM 0xabcd0001
#define IOCTL_REMOVE_ITEM 0xabcd0002
#define IOCTL_SKIP 0xabcd0003
#define IOCTL_EDIT_MEMO 0xabcd0004

struct list_item {
  long key;
  struct list_head list;
  char memo[0x28];
};

struct req_item {
  long key;
  char memo[0x28];
};

static struct kmem_cache *item_cache;

static LIST_HEAD(g_head);
static DEFINE_MUTEX(g_mutex);

static int skip_item(long key) {
  struct list_item *cur, *next, *prev;
  struct list_head *pos, *temp;

  if (list_empty(&g_head))
    return 0;

  list_for_each_safe(pos, temp, &g_head) {
    if (pos->prev == &g_head)
      continue;
    if (pos->next == &g_head)
      break;

    cur = list_entry(pos, struct list_item, list);
    prev = list_entry(pos->prev, struct list_item, list);
    next = list_entry(pos->next, struct list_item, list);

    if (cur->key == key) {
      prev->list.next = cur->list.next;
      next->list.next = prev->list.next;

      next->list.prev = cur->list.prev;
      prev->list.prev = cur->list.prev;

      kmem_cache_free(item_cache, pos);
      return 0;
    }
  }

  return -EINVAL;
}

static int add_item(long key) {
  struct list_item *new_item;

  new_item = kmem_cache_alloc(item_cache, GFP_KERNEL);
  if (!new_item) {
    return -ENOMEM;
  }

  new_item->key = key;
  list_add_tail(&new_item->list, &g_head);

  return 0;
}

static int remove_item(long key) {
  struct list_item *item, *temp;

  list_for_each_entry_safe(item, temp, &g_head, list) {
    if (item->key == key) {
      list_del(&item->list);
      kmem_cache_free(item_cache, item);
      return 0;
    }
  }

  return -EINVAL;
}

static int edit_memo(struct req_item *req) {
  struct list_item *item;

  list_for_each_entry(item, &g_head, list) {
    if (item->key == req->key) {
      memcpy(&item->memo, &req->memo, sizeof(((struct list_item *)0)->memo));
      return 0;
    }
  }

  return -EINVAL;
}

static long device_ioctl(struct file *file, unsigned int cmd,
                         unsigned long arg) {
  long val;
  int ret = 0;
  struct req_item req;

  mutex_lock(&g_mutex);

  switch (cmd) {
  case IOCTL_ADD_ITEM:
    if (copy_from_user(&val, (long *)arg, sizeof(long))) {
      ret = -EFAULT;
      goto end;
    }
    ret = add_item(val);
    break;

  case IOCTL_REMOVE_ITEM:
    if (copy_from_user(&val, (long *)arg, sizeof(long))) {
      ret = -EFAULT;
      goto end;
    }
    ret = remove_item(val);
    break;
  case IOCTL_SKIP:
    if (copy_from_user(&val, (long *)arg, sizeof(long))) {
      ret = -EFAULT;
      goto end;
    }
    ret = skip_item(val);
    break;
  case IOCTL_EDIT_MEMO:
    if (copy_from_user(&req, (void *)arg, sizeof(struct req_item))) {
      ret = -EFAULT;
      goto end;
    }
    ret = edit_memo(&req);
    break;
  default:
    ret = -EINVAL;
  }
end:
  mutex_unlock(&g_mutex);

  return ret;
}

// --- initialization -- //
static struct file_operations chal_fops = {
    .owner = THIS_MODULE,
    .unlocked_ioctl = device_ioctl,
};
static struct miscdevice chal_device = {
    .minor = MISC_DYNAMIC_MINOR,
    .name = DEVICE_NAME,
    .fops = &chal_fops,
};

static int __init module_initialize(void) {
  if (misc_register(&chal_device)) {
    pr_warn("Failed to register\n");
    return -EBUSY;
  }
  item_cache = kmem_cache_create(CACHE_NAME, sizeof(struct list_item), 0,
                                 SLAB_HWCACHE_ALIGN, NULL);
  if (!item_cache) {
    pr_warn("Failed to create slab cache\n");
    return -ENOMEM;
  }
  INIT_LIST_HEAD(&g_head);
  return 0;
}

module_init(module_initialize);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("LLM and Rona");
MODULE_DESCRIPTION("vibexec - Kernel module for IERAE CTF 2025");
