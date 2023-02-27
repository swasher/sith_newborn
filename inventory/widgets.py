# coding: utf-8
from django.utils.safestring import mark_safe
from django.contrib.admin.widgets import AdminFileWidget
import cloudinary


class AdminCloudinaryWidget(AdminFileWidget):

    #template_with_initial = ('%(initial_text)s: <a href="%(initial_url)s">%(initial)s</a> %(clear_template)s<br />%(input_text)s: %(input)s')
    # override:
    template_with_initial = ''

    #template_with_clear = '%(clear)s <label for="%(clear_checkbox_id)s">%(clear_checkbox_label)s</label>'
    # override:
    template_with_clear = ''

    def render(self, name, value, attrs=None):
        output = []
        cloudinary_prefix = 'https://cloudinary.com/console/media_library#/dialog/image/upload/'


        if value and getattr(value, "url", None):
            try:
                file_format = cloudinary.api.resource(value.public_id)['format']
            except (cloudinary.api.NotFound, AttributeError):
                file_format = None

            try:
                caption = cloudinary.api.resource(value.public_id)['context']['custom']['caption']
            except (cloudinary.api.NotFound, KeyError):
                caption = '<br>'

            try:
                alt = cloudinary.api.resource(value.public_id)['context']['custom']['alt']
            except (cloudinary.api.NotFound, KeyError):
                alt = "Image does't exist"

            picture_preview = cloudinary.CloudinaryImage(value.public_id).image(format='JPG', width = 150, height = 150, crop = 'fill', alt = alt) # html TAG 'a' with a small pict
            picture_full = cloudinary.CloudinaryImage(value.public_id).build_url()                                                                 # http link to full pict
            picture_featherlight = '<a href="{}" data-featherlight="image" class="featherlight-loading">{}</a>'.format(picture_full, picture_preview)
            picture_simple = '<a href={}  target="_blank" alt="{}">{}</a>'.format(picture_full, alt, picture_preview)
            cloudinary_link = '<a href="{}{}" target="_blank">Cloudinary Link</a>'.format(cloudinary_prefix, value.public_id)                      # html TAG 'a' with text link

            if file_format in ['jpg', 'jpeg', 'png', 'gif']:
                picture = picture_featherlight
            else:
                picture = picture_simple

            output.append('<div>{}</div>'.format(caption))
            output.append('<div>{}</div>'.format(picture))
            output.append('<div>{}</div>'.format(cloudinary_link))

        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))