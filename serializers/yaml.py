""" pretty serialization for yaml """
import yaml
from django.core.serializers.pyyaml import (  # IGNORE:W0611
    Serializer as YamlSerializer, DjangoSafeDumper,
    Deserializer)  # @UnusedImport


class Serializer(YamlSerializer):
    """ utf8-friendly dumpdata management command """
    def end_serialization(self):
        yaml.dump(self.objects, self.stream, allow_unicode=True,
                  default_flow_style=False,
                  Dumper=DjangoSafeDumper, **self.options)