#include <linux/module.h>
#include <linux/export-internal.h>
#include <linux/compiler.h>

MODULE_INFO(name, KBUILD_MODNAME);

__visible struct module __this_module
__section(".gnu.linkonce.this_module") = {
	.name = KBUILD_MODNAME,
	.init = init_module,
#ifdef CONFIG_MODULE_UNLOAD
	.exit = cleanup_module,
#endif
	.arch = MODULE_ARCH_INIT,
};



static const struct modversion_info ____versions[]
__used __section("__versions") = {
	{ 0x71abd973, "snd_hda_find_mixer_ctl" },
	{ 0xaf53b79c, "snd_hda_override_amp_caps" },
	{ 0x88b75d86, "_dev_err" },
	{ 0xf88b3281, "__hda_codec_driver_register" },
	{ 0x30ed5881, "snd_hda_parse_pin_defcfg" },
	{ 0xefb490ad, "snd_hda_gen_init" },
	{ 0xbd03ed67, "random_kmalloc_seed" },
	{ 0x9aa6980d, "mutex_lock" },
	{ 0xf729afc7, "snd_hda_gen_stream_pm" },
	{ 0xd142ad0a, "snd_hda_gen_fix_pin_power" },
	{ 0xcfc17774, "_snd_hda_set_pin_ctl" },
	{ 0xd272d446, "__x86_return_thunk" },
	{ 0x1ee7289e, "snd_hda_gen_update_outputs" },
	{ 0x82fd7238, "__ubsan_handle_shift_out_of_bounds" },
	{ 0x86750c5f, "snd_hda_jack_unsol_event" },
	{ 0x4131f769, "dmi_match" },
	{ 0xefb490ad, "snd_hda_gen_build_pcms" },
	{ 0x9aa6980d, "mutex_unlock" },
	{ 0xcc1d5ac5, "param_ops_bool" },
	{ 0xce56ea17, "__kmalloc_cache_noprof" },
	{ 0x75e46e8a, "snd_hda_pick_fixup" },
	{ 0x967c6a6c, "snd_hda_apply_fixup" },
	{ 0x239d3735, "snd_hda_gen_parse_auto_config" },
	{ 0xe4de56b4, "__ubsan_handle_load_invalid_value" },
	{ 0xf874eb37, "snd_hdac_codec_read" },
	{ 0xa65b83f9, "kmalloc_caches" },
	{ 0xefb490ad, "snd_hda_gen_build_controls" },
	{ 0xff4007e6, "query_amp_caps" },
	{ 0xd2b62a15, "snd_hda_gen_spec_init" },
	{ 0xc05fdb41, "snd_hda_codec_setup_stream" },
	{ 0x0acdf7ed, "hda_codec_driver_unregister" },
	{ 0x14373bcf, "snd_hda_apply_pincfgs" },
	{ 0xcbd32b17, "snd_hda_codec_get_pincfg" },
	{ 0xf874eb37, "snd_hdac_codec_write" },
	{ 0x1ee7289e, "snd_hda_gen_remove" },
	{ 0xfffc5e2f, "snd_hda_codec_pcm_new" },
	{ 0xf1ea125c, "__snd_hda_codec_cleanup_stream" },
	{ 0xd272d446, "__fentry__" },
	{ 0x5a844b26, "__x86_indirect_thunk_rax" },
	{ 0x88b75d86, "_dev_info" },
	{ 0x90a48d82, "__ubsan_handle_out_of_bounds" },
	{ 0xd12785c5, "snd_hda_sequence_write" },
	{ 0xe9196a28, "module_layout" },
};

static const u32 ____version_ext_crcs[]
__used __section("__version_ext_crcs") = {
	0x71abd973,
	0xaf53b79c,
	0x88b75d86,
	0xf88b3281,
	0x30ed5881,
	0xefb490ad,
	0xbd03ed67,
	0x9aa6980d,
	0xf729afc7,
	0xd142ad0a,
	0xcfc17774,
	0xd272d446,
	0x1ee7289e,
	0x82fd7238,
	0x86750c5f,
	0x4131f769,
	0xefb490ad,
	0x9aa6980d,
	0xcc1d5ac5,
	0xce56ea17,
	0x75e46e8a,
	0x967c6a6c,
	0x239d3735,
	0xe4de56b4,
	0xf874eb37,
	0xa65b83f9,
	0xefb490ad,
	0xff4007e6,
	0xd2b62a15,
	0xc05fdb41,
	0x0acdf7ed,
	0x14373bcf,
	0xcbd32b17,
	0xf874eb37,
	0x1ee7289e,
	0xfffc5e2f,
	0xf1ea125c,
	0xd272d446,
	0x5a844b26,
	0x88b75d86,
	0x90a48d82,
	0xd12785c5,
	0xe9196a28,
};
static const char ____version_ext_names[]
__used __section("__version_ext_names") =
	"snd_hda_find_mixer_ctl\0"
	"snd_hda_override_amp_caps\0"
	"_dev_err\0"
	"__hda_codec_driver_register\0"
	"snd_hda_parse_pin_defcfg\0"
	"snd_hda_gen_init\0"
	"random_kmalloc_seed\0"
	"mutex_lock\0"
	"snd_hda_gen_stream_pm\0"
	"snd_hda_gen_fix_pin_power\0"
	"_snd_hda_set_pin_ctl\0"
	"__x86_return_thunk\0"
	"snd_hda_gen_update_outputs\0"
	"__ubsan_handle_shift_out_of_bounds\0"
	"snd_hda_jack_unsol_event\0"
	"dmi_match\0"
	"snd_hda_gen_build_pcms\0"
	"mutex_unlock\0"
	"param_ops_bool\0"
	"__kmalloc_cache_noprof\0"
	"snd_hda_pick_fixup\0"
	"snd_hda_apply_fixup\0"
	"snd_hda_gen_parse_auto_config\0"
	"__ubsan_handle_load_invalid_value\0"
	"snd_hdac_codec_read\0"
	"kmalloc_caches\0"
	"snd_hda_gen_build_controls\0"
	"query_amp_caps\0"
	"snd_hda_gen_spec_init\0"
	"snd_hda_codec_setup_stream\0"
	"hda_codec_driver_unregister\0"
	"snd_hda_apply_pincfgs\0"
	"snd_hda_codec_get_pincfg\0"
	"snd_hdac_codec_write\0"
	"snd_hda_gen_remove\0"
	"snd_hda_codec_pcm_new\0"
	"__snd_hda_codec_cleanup_stream\0"
	"__fentry__\0"
	"__x86_indirect_thunk_rax\0"
	"_dev_info\0"
	"__ubsan_handle_out_of_bounds\0"
	"snd_hda_sequence_write\0"
	"module_layout\0"
;

MODULE_INFO(depends, "snd-hda-codec,snd-hda-codec-generic,snd-hda-core");

MODULE_ALIAS("hdaudio:v10134206r*a01*");
MODULE_ALIAS("hdaudio:v10134207r*a01*");
MODULE_ALIAS("hdaudio:v10134208r*a01*");

MODULE_INFO(srcversion, "51E4CD1B66481DA40ABC644");
