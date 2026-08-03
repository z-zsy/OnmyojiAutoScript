# This Python file uses the following encoding: utf-8
from module.atom.image import RuleImage
from tasks.Dokan.assets import DokanAssets


class DokanSelfAssets(DokanAssets):
    I_XIN_ICON = RuleImage(
        roi_front=(0, 0, 1280, 720),
        roi_back=(0, 0, 1280, 720),
        threshold=0.75,
        method="Template matching",
        file="./user_tasks/DokanSelf/res/xin_icon.png"
    )
