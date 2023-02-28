from django.db.models.signals import pre_save, pre_delete, post_save, post_delete
from django.dispatch import receiver

from .models import Component
from .models import Computer


@receiver(pre_delete, sender=Component)
def update_pc_memory_on_delete_pre(sender, instance, **kwargs):
    if instance.sparetype.name == 'memory' and instance.container.kind == 'PC':
        instance._pc_pk = Component.objects.get(pk=instance.pk).container.pk


@receiver(post_delete, sender=Component)
def update_pc_memory_on_delete_post(sender, instance, **kwargs):
    if instance.sparetype.name == 'memory' and instance.container.kind == 'PC':
        try:
            pc = Computer.objects.get(pk=instance._pc_pk)
        except Computer.DoesNotExist:
            pass
        else:
            pc.update_memory()


@receiver(pre_save, sender=Component)
def update_pc_memory_pre(sender, instance, **kwargs):
    """
    Задача pre_save - при переносе модуля памяти определить предыдущего владельца.

    В pre_save нельзя вызывать update_ram, потому что предыдущий владелец (Computer) еще содержит
    удаляемую из него память (Component `memory`). Поэтому используется хак с передачей pk через protected атрибут
    """
    if instance.pk:
        if instance.sparetype.name == 'memory':
            # Извлекать pk можно только таким образом, что-то вроде instance.container.pk работать не будет
            instance._previous_PC_pk = Component.objects.get(pk=instance.pk).container.pk


@receiver(post_save, sender=Component)
def update_pc_memory_post(sender, instance, **kwargs):
    """
    В post_save мы вызываем update_memory для предущего и текущего владельца-компьютера
    """

    if instance.sparetype.name == 'memory':
        try:
            previous_pc = Computer.objects.get(pk=instance._previous_PC_pk)
        except AttributeError:
            # Если объект создавался вручную (Добавить Компонент в Комптютер), то для него не
            # вызывался pre_save, и соотв. не существует _previous_PC_pk.
            pass
        except Computer.DoesNotExist:
            # Компонент ранее принадлежал не Компьютеру, а Контейнеру (комнате, например)
            pass
        else:
            #if instance.container.kind == 'PC':
            previous_pc.update_memory()

        try:
            new_pc = Computer.objects.get(pk=instance.container.pk)
        except Computer.DoesNotExist:
            # Компонент переносится не в Компьютер, а, например, в комнату
            pass
        else:
            new_pc.update_memory()



