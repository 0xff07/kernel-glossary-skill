# DRM/KMS knowledge-base campaign: plan

## Context

Campaign short name: `drm`. Campaign file: `progress/drm.md`; artifact directory: `progress/drm/` (dossiers, lint/verify reports, parity tables, audit reports land there; nothing outside it).

Request source: `prompt.md` at the documented tree's root — an in-depth, fine-grained DRM/KMS documentation set for the Linux kernel, output under a new `docs/drm/` of the kernel-glossary skill (`${CLAUDE_SKILL_DIR}/docs/drm/`). The prompt's own words: "The topic list is very rough. Curate new pages where you see fit"; "Prefer finer granularity whenever possible"; "Make sure you cover all the major structures for Linux kernel defined under the files in the 'drivers/gpu/drm/' directory"; "Don't just create pure conceptual pages"; "!!!IMPORTANT!!!: Don't limit yourself to 100-400 lines per page. Do as detailed as you can."

Documented tree: the local Linux checkout, tag `v7.0`, commit `028ef9c96e96` ("Linux 7.0"). semcode index complete at that commit; all Elixir links use `https://elixir.bootlin.com/linux/v7.0/source/...`. Subsystem Map entry DRM (`guidelines/reference/subsystems.md`): dir `drm`, tag `graphics`, kernel_paths `drivers/gpu/drm/`, `include/drm/`, `include/uapi/drm/`, spec none, section6_heading INTERFACES.

Stale-session inputs (hints only, never evidence):
- Two superseded plan files at the tree root, left by earlier dead sessions. The first planned ~77 pages (34 per-fourcc format pages); the second superseded it (the user chose ~7 family-grouped format pages, pixel-section-first order) and recorded a full-corpus draft audit. Both predate the current skill restructure (passes, dossiers, parity tables, Gate A/B, rules 7l-7r), so their LOCKED STANDARDS sections are superseded by `guidelines/`; only their user scope decisions and topic curation survive as hints, re-confirmed at the checkpoint below.
- Draft corpus (primary): a prior-generation draft set produced on an earlier working branch of the skill repository, 64 pages under `docs/drm/` (150-1,334 lines each), extracted read-only for audit. Corpus-wide quick census: all 15,442 Elixir links already v7.0; 0 em-dashes; 384 "vtable" hits (banned word); 158 "fbdev" hits (banned scope); provenance comments in single-excerpt form, many marked "kerneldoc elided" (excerpts non-verbatim, fails the byte-compare check); ~202 box-drawing figure blocks.
- Draft corpus (secondary): an older-generation corpus in a separate checkout at kernel v6.19, 30 primitive pages (82-278 lines). Scaffolding at most; the primary draft corpus supersedes it except possibly OTHER SOURCES links.

NOT inputs: the other campaigns' entries under `progress/` (other runs, isolation per SKILL.md, "The three artifacts and the two states"); `guidelines/reference/samples/` pages (style/depth calibration only, never kernel facts). The existing `docs/dp/` knowledge base (69 pages: AUX, DPCD, link training, MST) is a boundary constraint, not an input: DP protocol internals stay in dp/, this campaign stops at the KMS↔DP-helper seam.

Output root: `docs/drm/`. No `SUMMARY.md`/`mkdocs.yml` edits. No git commits without an explicit user go.

## Status

This section IS the campaign's log and its only memory (`guidelines/passes/plan.md`): every durable event is appended here at the moment it happens, and nothing else travels — the dossiers under `progress/<campaign>/` are scratch. The entries below are shape illustrations with <placeholders>, not a real log; a live campaign accumulates entries of these shapes, newest appended last:

- [<date>] Campaign started. Name `<campaign>` chosen (existing `progress/` entries listed for the name-collision check only). Workspace created: `progress/<campaign>.md`, `progress/<campaign>/`. Tree pinned `<tag>` @ `<sha>`; Elixir tag confirmed.
- [<date>] Phase 1 inventory dispatched: <n> parallel read-only agents, one per area.
- [<date>] Phase 1 complete: one digest per area recorded under Inventory findings; version-drift headline: <renames and removals>.
- [<date>] Phase 2 catalog drafted: <n> groups, <n> rows (<n> [prompt] / <n> [curated]), fold-ins, boundary rules, batch order. Adversarial plan review dispatched.
- [<date>] Phase 2 review complete: <n> amendments accepted, <n> declined with reasoning (recorded under the review outcome). Catalog now <n> rows.
- [<date>] Phase 3 user checkpoint: catalog and scope questions presented; decisions recorded under Scope decisions; explicit go received.
- [<date>] B<n> dispatched: one writer per page (<slugs>).
- [<date>] B<n> checkpoint: <done>/<total> pages WRITTEN → LINTED; <n> escalations adjudicated (<accepted>/<declined>); per-page statistics recorded.
- [<date>] AMENDMENT: <the user's instruction, verbatim where short, and what it supersedes; also recorded in the dated amendments under Execution & verification>.
- [<date>] CORRECTION: <an earlier recorded claim> is wrong; <the re-verified fact and the measurement that established it>.
- [<date>] LESSON: <a checker false-positive class, a settled linking adjudication, a pipeline fix; surfaced to the user, who alone folds a ruling into 7r>.

## Scope decisions

### Hard constraints from prompt.md (verbatim or near-verbatim)

1. "Focus on x86-64, ACPI-based systems. Do not include any DT-based system or drivers."
2. Driver examples: amdgpu and Intel i915/xe ONLY. "For amdgpu, if you need specific IP, use DCN35 as an example, but only mention this when it's relevant. Don't mention it if the code you're citing is generic. Always put amdgpu drivers before the i915/xe in terms of section ordering."
3. "For the DETAILS section, generic sections should be put before specific channel coding-specific/driver-specific sections."
4. "For all the behaviors mentioned in the topic list, you must point out all the places in the linux kernel that match the behavior, and cite the source code accordingly. Cite as many and as complete as possible." (rule 7j)
5. "DO NOT MENTION fbdev and tty layer." "DO NOT COVER MIPI-DSI." "Assume we are displaying through a DisplayPort or eDP."
6. "Make sure you also include as all relevant tracepoints and possible tracing events as possible. Explicitly mention them in the pages if there's any." (campaign delta: inventory digests carry a 7th item, tracepoints per area)
7. "The pages ... should focus heavily on how Linux kernel internally tracking/representing some of the major constructs for displaying. Make sure for every concept you also mention corresponding parts in the Linux kernel source code that interacts with that concept."
8. "Draw ASCII diagrams to illustrate, but do not just draw the code enumerating flow graphs." (7g-7i structural/spatial figures, no call-graph charts)
9. "You must use semcode tools." "You must not use hedging wordings."
10. Prior drafts exist and are "too rough to use. Make sure you rephrase them before reusing." (rule 7p and `guidelines/passes/plan.md`, "Deriving from prior drafts and pages", govern)

### User-confirmed decisions (checkpoint answers, 2026-07-12 — these supersede the inherited hints I1-I3 below)

1. Format-page granularity: "Families now, split later" — the 7 family pages ship in this campaign; per-fourcc splitting is a recorded possible follow-up round, not part of this catalog.
2. Optional peripheral rows: "Keep all 3" — writeback, privacy-screen, panic stay; the 77-page total stands.
3. Draft posture: "Write everything fresh" — neither draft corpus is an input to writers; every page is researched and written from the v7.0 tree alone. The Draft reuse map below is downgraded to reference/evidence (audit record), and writer briefs carry no draft pointers. (Overrides inherited I2 and voids the second stale plan's figure-preservation guarantee; the request's "rephrase before reusing" clause is moot since nothing is reused.)
4. Batch order: "Foundational-first" — the B1-B19 order as amended by review stands.

Explicit go: received 2026-07-12 via the checkpoint answers (catalog confirmed by decisions 1-2, execution order selected by decision 4). Per campaign mode, pages save without per-page asks; git commits still require a separate user go.

### Inherited stale-session decisions (superseded record; kept for reference)

- I1. Format-page granularity: family-grouped per plan2 decision 3 (→ confirmed as decision 1 above).
- I2. Draft posture: mine the primary draft corpus per 7p (→ OVERRIDDEN by decision 3: write fresh).
- I3. plan2's "pixel-section-first" priority motivation void (→ confirmed foundational-first as decision 4).

## Inventory findings

(One compact digest per area, recorded verbatim from the inventory agents; pending.)

### Area A: pixel formats & color management — COMPLETE (recorded 2026-07-12)

#### 1. Core structs (field groups · role · file:line)
- struct drm_format_info — `format` 4CC; `depth`(legacy); `num_planes`; union `cpp[4]`/`char_per_block[4]`; `block_w[4]`/`block_h[4]`; `hsub`/`vsub`; bools `has_alpha`/`is_yuv`/`is_color_indexed`. Describes one pixel format. `include/drm/drm_fourcc.h:61`
- struct drm_framebuffer — `dev`,`head`,`base`(refcount mode_object),`format`,`funcs`,`pitches[4]`,`offsets[4]`,`modifier`,`width`/`height`,`flags`/`internal_flags`,`obj[4]`. Scanout buffer. `include/drm/drm_framebuffer.h:120`; drm_afbc_framebuffer (afbc block/aligned dims) `:295`
- struct drm_color_lut — `red/green/blue/reserved` u16 (0..0xffff→0..1.0). `include/uapi/drm/drm_mode.h:864`
- struct drm_color_lut32 — u32 per channel (extended). `:880`
- struct drm_color_ctm — `matrix[9]` S31.32 sign-magnitude 3x3. `:837`; drm_color_ctm_3x4 `matrix[12]` `:850`
- struct hdr_metadata_infoframe — `eotf`,`metadata_type`,`display_primaries[3]`,`white_point`,`max/min_display_mastering_luminance`,`max_cll`,`max_fall`. `:1016`; hdr_output_metadata (`metadata_type`+union `hdmi_metadata_type1`) `:1080`
- struct drm_colorop — `dev`,`head`(mode_config.colorop_list),`index`,`base`,`plane`,`state`,`properties`,`type`,`next`,+ per-type props (`type_/bypass_/size_/curve_1d_type_/multiplier_/lut1d_/lut3d_interpolation_/data_/next_property`),`size`. One color-pipeline op. `include/drm/drm_colorop.h:201`; drm_colorop_state (`bypass`,`curve_1d_type`,`multiplier`,`data` blob,`state`) `:140`
- struct intel_color_funcs — hooks `color_check`,`color_commit_noarm/arm`,`color_post_update`,`load_luts`,`read_luts`,`lut_equal`,`read_csc`,`get_config`,`load_plane_csc_matrix`,`load_plane_luts`. i915 function pointer struct. `drivers/gpu/drm/i915/display/intel_color.c:38`
- struct drm_display_info (sink) — `bpc` `:695`, `color_formats` `:722`, `edid_hdmi_rgb444/ycbcr444_dc_modes` `:784/790`, `hdmi`, `hdr_sink_metadata` `:805`, `monitor_range`. `include/drm/drm_connector.h:681`
- struct drm_connector_state color fields — `colorspace` `:1108`, `max_requested_bpc` `:1127`, `max_bpc` `:1133`, `hdr_output_metadata` blob `:1145`. `include/drm/drm_connector.h`
- Enums: drm_colorop_type {1D_CURVE,1D_LUT,CTM_3X4,MULTIPLIER,3D_LUT} `uapi drm_mode.h:894`; drm_colorop_curve_1d_type {sRGB (INV) EOTF, PQ_125 (INV) EOTF, BT2020 (INV) OETF, GAMMA22 (_INV), _COUNT} `drm_colorop.h:42`; lut3d/lut1d_interpolation_type `uapi:972/984`; drm_color_encoding {BT601,BT709,BT2020,_MAX} `drm_color_mgmt.h:103`; drm_color_range {LIMITED,FULL,_MAX} `:110`; drm_color_lut_tests {EQUAL_CHANNELS,NON_DECREASING} `:128`; drm_colorspace `drm_connector.h:533`

#### 2. API families (entry · file:line · role)
- FourCC/format-info (`drm_fourcc.c`): `__drm_format_info` :175 (the format table), `drm_format_info` :407, `drm_get_format_info` :427 (driver `.get_format_info` override→core), `drm_format_info_block_width/height` :452/472, `drm_format_info_bpp` :492, `drm_format_info_min_pitch` :513; legacy `drm_mode_legacy_fb_format` :40, `drm_driver_legacy_fb_format` :118, `drm_driver_color_mode_format` :158.
- Format accessor inlines (`drm_fourcc.h`): `drm_format_info_is_yuv_packed/semiplanar/planar` :154/168/182, `_is_yuv_sampling_410..444` :197-260, `_plane_width/_plane_height` :272/294.
- CRTC color-mgmt (`drm_color_mgmt.c`): `drm_crtc_enable_color_mgmt` :166, `drm_mode_crtc_set_gamma_size` :208, `drm_crtc_legacy_gamma_set` :277, `drm_mode_gamma_set/get_ioctl` :361/430, `drm_plane_create_color_properties` :531, `drm_color_lut_check` :606, `drm_color_lut32_check` :889, `drm_color_ctm_s31_32_to_qm_n` :136, name getters `drm_get_color_encoding/range_name` :492/508.
- Gamma/palette HW-programming helpers (`drm_color_mgmt.c`): `drm_crtc_load_gamma_888` :651, `_565_from_888` :671, `_555_from_888` :701, `drm_crtc_fill_gamma_888/565/555` :733/759/788, `drm_crtc_load_palette_8` :810, `drm_crtc_fill_palette_332/8` :840/869 (typedef `drm_crtc_set_lut_func` `drm_color_mgmt.h:154`).
- LUT inlines (`drm_color_mgmt.h`): `drm_color_lut_extract` :43, `drm_color_lut32_extract` :61, `drm_color_lut_size` :86, `drm_color_lut32_size` :98.
- Colorop / color pipeline (`drm_colorop.c`): `drm_plane_colorop_curve_1d_init` :212, `_curve_1d_lut_init` :296, `_ctm_3x4_init` :341, `_mult_init` :369, `_3dlut_init` :392; `drm_colorop_cleanup` :164, `_pipeline_destroy` :188, `_reset` :514, `_atomic_duplicate_state` :448, `_atomic_destroy_state` :463, `_set_next_property` :592; property maker `drm_plane_create_color_pipeline_property` `drm_plane.c:1838` (COLOR_PIPELINE).
- Connector color props (`drm_connector.c`): `drm_connector_attach_max_bpc_property` :2831, `..._hdr_output_metadata_property` (~:2855; blob prop created :1860), `drm_mode_create_hdmi/dp_colorspace_property` :2623/2648, `drm_mode_create_colorspace_property` :2568, `drm_display_info_set_bus_formats` :1189, `drm_get_colorspace_name` :1364, `drm_hdmi_connector_get_broadcast_rgb_name` :1418, `_get_output_format_name` :1443.
- Plane IN_FORMATS advertising (`drm_plane.c`): blob builder `create_in_formats` (~:205-250, emits `count_formats`/`count_modifiers`, `format_types`), `__drm_universal_plane_init` :360 (stores `format_types`/`modifiers`).
- DP bpc seam (`intel_dp.c`): `intel_dp_max_bpp` :1691 (clamps `pipe_bpp/3` by `dfp.max_bpc`, HDMI bpc, eDP VBT vs `display_info.bpc`), `intel_dp_min_bpp` :1180, `intel_dp_output_format_link_bpp_x16` :1188, `intel_dp_dsc_compute_max_bpp` uses `max_requested_bpc` :1862. Seam ends here: bpc/bpp feed link config; AUX/DPCD/link-training is out of scope.

#### 3. Lifecycle & locking
- Legacy gamma store: `crtc->gamma_store` kcalloc'd in `drm_mode_crtc_set_gamma_size` (`drm_color_mgmt.c:216`), sized `crtc->gamma_size`; set/get ioctls copy in/out. Set path takes `DRM_MODESET_LOCK_ALL_BEGIN/END` (`:385/410`); get path `drm_modeset_lock(&crtc->mutex)` (`:450`).
- LUT/CTM blobs: `drm_property_create_blob`+`drm_property_replace_blob`; atomic state carries `degamma_lut`/`ctm`/`gamma_lut` and `color_mgmt_changed` flag set on replace (`:337`); applied via `drm_atomic_commit`.
- Framebuffer: refcount in `base.refcount`; `drm_framebuffer_get/put` (`drm_framebuffer.h:229/241`), `drm_framebuffer_init/cleanup/remove` (`:213/220/219`); listed on `mode_config.fb_list` under `fb_lock` (`drm_for_each_fb` :283).
- Colorop: no own lock ("locked and programmed along with associated drm_plane"); `state` protected by plane mutex; `index`/`head` invariant over dev lifetime; created per-plane, torn down by `drm_colorop_pipeline_destroy`, reset via `drm_colorop_reset`/`__drm_colorop_state_reset`.
- Connector bpc: `drm_connector_attach_max_bpc_property` seeds `state->max_requested_bpc = state->max_bpc = max` (`:2847-2848`); requires prior `funcs->reset` for state.

#### 4. Hard-coded limits (value · file:line)
- `DRM_FORMAT_MAX_PLANES` = 4u `drm_fourcc.h:32` (planes 1-3 used).
- Plane `format_count` ≤ 64: `WARN_ON(format_count > 64)` `drm_plane.c:386`.
- Generic format table: ~130 entries `__drm_format_info` `drm_fourcc.c:177-384`.
- `LEGACY_LUT_LENGTH` = 256 `intel_color.c:117`.
- amdgpu `MAX_COLOR_LUT_ENTRIES` = 4096, `MAX_COLOR_LEGACY_LUT_ENTRIES` = 256 `amdgpu_dm.h:1072/1074`; amdgpu `LUT3D_SIZE` = 17 `amdgpu_dm_colorop.c:56`.
- HDMI `max_bpc` must be 8/10/12 `drm_connector.c:600`; property range min..max via `drm_property_create_range` `:2839`.
- CTM sizes: `matrix[9]` / 3x4 `matrix[12]`; `ctm_s31_32_to_qm_n` `WARN_ON(m>32||n>32)` `drm_color_mgmt.c:142`.
- i915 HW LUT sizes: `ivb_lut_10_size` 512/1024 `intel_color.c:1443`; `glk_degamma_lut_size` 131/35 `:1586`; per-platform `.gamma_lut_size` 256/129/257/1024/262145, `.degamma_lut_size` 33/65/129/1024 `intel_display_device.c:202-225`.
- `MAX_HW_POINTS = NUM_PTS_IN_REGION(16)*NUM_REGIONS` `color_table.h:32/34`.
- Enum bounds: `DRM_COLOR_ENCODING_MAX`=3, `DRM_COLOR_RANGE_MAX`=2.

#### 5. Version-specific facts (v7.0 vs older docs)
- NEW: per-plane color pipeline / drm_colorop exists — core `drivers/gpu/drm/drm_colorop.c` + `include/drm/drm_colorop.h`; plane `COLOR_PIPELINE` property `drm_plane.c:1838`; `enum drm_colorop_type` {1D_CURVE,1D_LUT,CTM_3X4,MULTIPLIER,3D_LUT} `uapi:894`. Driver impls new: `amdgpu_dm_colorop.c`, i915 `intel_colorop.c` + `intel_color_pipeline.c` (`_intel_color_pipeline_plane_init` :17, `intel_color_pipeline_plane_init` :81).
- NEW: `struct drm_color_ctm_3x4` (matrix[12]) `uapi:850`; `struct drm_color_lut32` (32-bit) `uapi:880` with helpers `drm_color_lut32_check` `drm_color_mgmt.c:889`, `drm_color_lut32_size/extract` `drm_color_mgmt.h:98/61`.
- NEW: 3D LUT properties present — `DRM_COLOROP_3D_LUT` + `lut3d_interpolation` (TETRAHEDRAL); `lut1d_interpolation` (LINEAR). Curve TF enum adds sRGB/PQ_125/BT2020/Gamma22 (+inverses).
- NEW generic gamma/palette programming helpers family (`drm_crtc_load_gamma_888`/`565`/`555`, `fill_gamma_*`, `load_palette_8`, `fill_palette_332/8`) — recent additions to `drm_color_mgmt.c`.
- New fourcc entries vs older tables: `R10`/`R12`, `RGB161616`/`BGR161616`, `D1/D2/D4/D8`, `VUY888`/`VUY101010`, planar `S010..S416`, `P030`, `NV15/NV20/NV30`, `Q410/Q401`.
- Legacy `drm_color_ctm` remains S31.32 sign-magnitude; classic CRTC props (DEGAMMA_LUT/CTM/GAMMA_LUT + *_SIZE) still primary path via `drm_crtc_enable_color_mgmt`.

#### 6. Suggested page topics (anchor symbols)
- bpc/bpp: `display_info.bpc`, `max_bpc`/`max_requested_bpc` props, `intel_dp_max_bpp`/`_min_bpp`, `drm_format_info_bpp`, connector `output_bpc`.
- Color formats — RGB family page: `__drm_format_info` RGB rows + driver `rgb_formats`/`skl_plane_formats`/`i965/vlv_primary_formats`.
- Color formats — YUV family page: YUV rows + `drm_format_info_is_yuv_*`; planar (`YUV420`,`NV12`,`P010`,`S*`) vs packed (`YUYV`,`XYUV8888`,`Y2xx`).
- Pitch/layout: `drm_format_info_min_pitch`, `char_per_block`/`block_w`/`block_h`, `drm_framebuffer.pitches/offsets/modifier`.
- Gamut/colorspace: `enum drm_colorspace`, `Colorspace` prop, `hdmi_colorspaces`/`dp_colorspaces`, HDR infoframe + `HDR_OUTPUT_METADATA`, Broadcast RGB.
- Color pipeline (degamma→CTM→gamma): DEGAMMA_LUT/CTM/GAMMA_LUT + `drm_colorop` chain via `next`.
- Color curves / transfer functions: `drm_colorop_curve_1d_type` (sRGB/PQ/BT2020/Gamma22), `color_gamma.c` `translate_from_linear_space`/`build_pq`.
- Gamma/degamma LUTs: `drm_color_lut`/`lut32`, `drm_color_lut_check`, `drm_color_lut_extract`, HW sizes.
- CTM/CSC: `drm_color_ctm`(+3x4), `drm_color_ctm_s31_32_to_qm_n`, i915 `intel_csc_matrix`/`ILK_CSC_COEFF_*`.

#### 7. Tracepoints & trace events
- None in the generic color code: no `trace_*` in `drm_color_mgmt.c`, `drm_fourcc.c`, `drm_colorop.c`, `drm_plane.c`, `drm_framebuffer.c` (confirmed empty).
- None in driver color code: no `trace_*` in `amdgpu_dm_color.c`, `color_gamma.c`, `intel_color.c` (confirmed empty).
- No color-specific `include/trace/events/` header exists (only unrelated `gpu_mem.h`). Instrumentation is via `drm_dbg_kms`/`DRM_DEBUG_KMS`, not tracepoints.

#### Plane format-array catalog (arrays actually advertised)
amdgpu — `amdgpu_dm_plane.c`
- `rgb_formats[14]` :50 — XRGB8888,ARGB8888,RGBA8888,XRGB2101010,XBGR2101010,ARGB2101010,ABGR2101010,XRGB16161616,XBGR16161616,ARGB16161616,ABGR16161616,XBGR8888,ABGR8888,RGB565
- `overlay_formats[9]` :67 — XRGB8888,ARGB8888,RGBA8888,XBGR8888,ABGR8888,RGB565,NV21,NV12,P010
- `video_formats[3]` :79 — NV21,NV12,P010 · `cursor_formats[1]` :85 — ARGB8888
- `alpha_formats[8]` :113 (per-pixel-alpha test) — ARGB8888,RGBA8888,ABGR8888,ARGB2101010,ABGR2101010,ARGB16161616,ABGR16161616,ARGB16161616F

i915/xe — `skl_universal_plane.c` (selected by `skl/glk/icl_get_plane_formats` :2482/2501/2514)
- `skl_plane_formats[15]` :34 — C8,RGB565,XRGB8888,XBGR8888,ARGB8888,ABGR8888,XRGB2101010,XBGR2101010,XRGB16161616F,XBGR16161616F,YUYV,YVYU,UYVY,VYUY,XYUV8888
- `skl_planar_formats[16]` :52 — skl_plane_formats + NV12
- `glk_planar_formats[19]` :71 — + NV12,P010,P012,P016
- `icl_sdr_y_plane_formats[19]` :93 — C8,RGB565,XRGB/XBGR/ARGB/ABGR8888,XRGB/XBGR/ARGB/ABGR2101010,YUYV,YVYU,UYVY,VYUY,Y210,Y212,Y216,XYUV8888,XVYU2101010 (no fp16)
- `icl_sdr_uv_plane_formats[23]` :115 — SDR_Y set + NV12,P010,P012,P016
- `icl_hdr_plane_formats[26]` :141 — adds XRGB/XBGR/ARGB/ABGR16161616F, NV12,P010/12/16, Y210/212/216, XVYU2101010, XVYU12_16161616, XVYU16161616

i915/xe — `i9xx_plane.c`
- `i8xx_primary_formats[4]` :29 — C8,XRGB1555,RGB565,XRGB8888
- `ivb_primary_formats[6]` :37 — C8,RGB565,XRGB8888,XBGR8888,XRGB2101010,XBGR2101010 (no fp16)
- `i965_primary_formats[7]` :47 — ivb set + XBGR16161616F
- `vlv_primary_formats[11]` :58 — + ARGB8888,ABGR8888,ARGB2101010,ABGR2101010,XBGR16161616F
### Area B: KMS objects & probe/init — COMPLETE (recorded 2026-07-12)

#### 1. Core structs (field groups · role · file:line)
- drm_mode_config — include/drm/drm_mode_config.h:360 — device-global KMS registry; groups: locks (mutex/connection_mutex/idr_mutex/fb_lock/blob_lock/connector_list_lock spinlock/panic_lock raw), object lists+counts (crtc/plane/encoder/connector/colorop/property/blob/privobj), idrs (object_idr/tile_idr, connector_ida), min/max dims, funcs/helper_private, poll fields, ~80 standard `struct drm_property *` pointers, cursor size, suspend_state.
- drm_mode_object — include/drm/drm_mode_object.h:55 — base of all KMS objects; id, type (DRM_MODE_OBJECT_*), *properties, kref refcount, free_cb (non-NULL ⇒ dynamic-lifetime object).
- drm_property — include/drm/drm_property.h:80 — property descriptor; head, base, flags (RANGE/ENUM/BITMASK/OBJECT/BLOB + ATOMIC/IMMUTABLE), name[DRM_PROP_NAME_LEN], num_values, *values, dev, enum_list.
- drm_property_blob — include/drm/drm_property.h:216 — refcounted binary blob; base, dev, head_global/head_file, length, data[] (created drm_property_create_blob).
- drm_framebuffer — include/drm/drm_framebuffer.h:120 — FB object; dev, head, base(refcount), comm, *format, *funcs, pitches/offsets[DRM_FORMAT_MAX_PLANES], modifier, w/h, flags/internal_flags, filp_head, obj[] GEM.
- drm_plane_state — include/drm/drm_plane.h:54 — atomic plane state; plane/crtc/fb/fence, crtc_x/y/w/h, src_x/y/w/h (16.16), hotspot, alpha/pixel_blend_mode/rotation/zpos/normalized_zpos, color_encoding/range, fb_damage_clips, src/dst rect, visible, scaling_filter, color_pipeline (drm_colorop), commit, state.
- drm_plane — include/drm/drm_plane.h:641 — plane object; dev, head, name, mutex(modeset_lock), base, possible_crtcs mask, format_types/count, modifiers/count, funcs, properties, type (PRIMARY/CURSOR/OVERLAY), index, helper_private, *state, alpha/zpos/rotation/blend_mode_property.
- drm_crtc_state — include/drm/drm_crtc.h:81 — atomic CRTC state; enable/active, mode/adjusted_mode, mode_blob, plane/connector/encoder masks, gamma_lut/degamma_lut/ctm blobs, event, commit, state.
- drm_crtc — include/drm/drm_crtc.h:943 — CRTC object; dev, port, head, name, mutex(modeset_lock), base, primary/cursor plane, index, cursor_x/y, enabled, mode/hwmode, x/y, funcs, gamma_size/store, helper_private, *state.
- drm_encoder — include/drm/drm_encoder.h:105 — encoder object; dev, head, base, name, encoder_type (DRM_MODE_ENCODER_TMDS for DP/HDMI), index, possible_crtcs/possible_clones masks, crtc, bridge_chain list, funcs/helper_private, debugfs_entry.
- drm_connector_state — include/drm/drm_connector.h:1005 — atomic connector state; connector, crtc, best_encoder, link_status, state, commit, tv, self_refresh_aware, hdr/colorspace/max_bpc/max_requested_bpc fields.
- drm_connector — include/drm/drm_connector.h:1938 — connector object; dev/kdev/attr/fwnode, head+global_connector_list_entry, base, name, mutex (guards registration_state), index, connector_type[_id], *_allowed flags, registration_state, modes/probed_modes lists, status, display_info@2066, funcs@2069, edid_blob_ptr@2080, path_blob_ptr, max_bpc@2088+prop, privacy_screen@2128+notifier+props, polled@2176, dpms, helper_private@2187, force@2192, epoch_counter@2208, possible_encoders@2215 mask, encoder, eld[MAX_ELD_BYTES]+eld_mutex@2229, tile_* fields, state@2294.
- drm_display_info — include/drm/drm_connector.h:681 — parsed sink caps (from EDID); width/height_mm, bpc, subpixel_order, panel_orientation, color_formats, bus_formats/flags, max_tmds_clock, dvi_dual, is_hdmi/has_audio/has_hdmi_infoframe (replace drm_detect_* calls), deep-color masks, cea_rev, struct drm_hdmi_info hdmi, monitor_range/quirks/mso.
- drm_bridge — include/drm/drm_bridge.h:1100 — bridge object; base is drm_private_obj, dev, encoder, chain_node/list, funcs, container, kref refcount@1131, unplugged, ops/type, HDMI/CEC/audio fields, ddc. Funcs struct drm_bridge_funcs@include/drm/drm_bridge.h:64.
- Funcs structs: drm_mode_config_funcs mode_config.h:47; drm_framebuffer_funcs framebuffer.h:43; drm_crtc_funcs crtc.h:413; drm_plane_funcs plane.h:300; drm_encoder_funcs encoder.h:40; drm_connector_funcs connector.h:1350.
- Helper funcs structs (drm_modeset_helper_vtables.h): drm_crtc_helper_funcs:61; drm_encoder_helper_funcs:501; drm_connector_helper_funcs:850 (get_modes/detect_ctx/mode_valid/best_encoder — DP detect seam); drm_plane_helper_funcs:1189; drm_mode_config_helper_funcs:1497.
- Writeback/privacy: drm_writeback_connector include/drm/drm_writeback.h:21; drm_privacy_screen include/drm/drm_privacy_screen_driver.h:50.
- Driver wrappers (embed base objects): amdgpu — amdgpu_framebuffer amdgpu_mode.h:299, amdgpu_crtc:460, amdgpu_encoder:533, amdgpu_connector:617; amdgpu_display_manager amdgpu_dm.h:351, amdgpu_dm_connector:760, dm_plane_state:895, dm_crtc_state:971, dm_connector_state:1016. i915/xe — intel_encoder intel_display_types.h:163, intel_connector:519, intel_plane_state:662, intel_crtc_state:1003, intel_crtc:1481, intel_plane:1575, intel_digital_port:1965 (xe reuses these via drivers/gpu/drm/xe/display/).

#### 2. API families (file:line · role)
- Mode-config init/cleanup: drmm_mode_config_init drm_mode_config.c:429 (devm-managed); drm_mode_config_reset:193; drm_mode_config_cleanup:517; drm_modeset_register_all:39 / _unregister_all:71 (calls per-object register_all).
- Object id/refcount/lookup: drm_mode_object_add drm_mode_object.c:80 / _register:87 / _unregister:106; __drm_mode_object_find:138 / drm_mode_object_find:177; drm_mode_object_get:213 / _put:196.
- Property attach/values: drm_object_attach_property drm_mode_object.c:235; drm_object_property_set_value:285 / _get_value:353 / _get_default_value:378.
- Property create: drm_property_create drm_property.c:97; _enum:162/_bitmask:210/_range:277/_signed_range:305/_object:332/_bool:369; _add_enum:390; _destroy:441; _create_blob:556 / blob_get:632 / blob_put:601.
- Blend/composition props: drm_plane_create_alpha_property drm_blend.c:225; _rotation:278; _zpos:375 / _zpos_immutable:414; _blend_mode:577.
- Framebuffer: drm_framebuffer_init drm_framebuffer.c:863; _cleanup:982; _unregister_private:951; drm_mode_addfb:118/_ioctl:149 (legacy); addfb2:330/_ioctl:354; drm_internal_framebuffer_create:260.
- Plane: drm_universal_plane_init drm_plane.c:532; register_all:641/unregister_all:665/cleanup:683; create_scaling_filter:1770; add_size_hints:1799; create_color_pipeline:1838.
- CRTC: drm_crtc_init_with_planes drm_crtc.c:360 / drmm_crtc_init_with_planes:442 / cleanup:502; register_all:110/unregister_all:127; create_fence:184; legacy drm_crtc_init drm_modeset_helper.c:145.
- Encoder: drm_encoder_init drm_encoder.c:163 / drmm_encoder_init:287 / cleanup:187; register_all:72/unregister_all:89.
- Connector: drm_connector_init drm_connector.c:402 / _dynamic_init:442 / _init_with_ddc:479 / drmm_connector_init:521 / drmm_connector_hdmi_init:571; register:837 / dynamic_register:906 / unregister:931 / register_all:972 / cleanup:758; attach_encoder:666; attach_edid_property:644; create_standard_properties:1813; set_link_status_property:2809; ida_init:117/ida_destroy:125.
- Connector iteration: drm_connector_list_iter_begin drm_connector.c:1049 / _next:1078 / _end:1124 (only safe walk of connector_list).
- Bridge: drm_bridge_add drm_bridge.c:371 / _remove:431 / _attach:499 / _get:292 / _put:308 / _detect:1338 (kref via __drm_bridge_free).
- Probe/detect/hotplug: drm_helper_probe_single_connector_modes drm_probe_helper.c:559; drm_helper_probe_detect:397 / _detect_ctx:357 (→ connector helper detect_ctx → driver DPCD/AUX seam); poll_init:924/_fini:937/drmm_poll_init:963/_enable:305/_disable:891/_reschedule:335; hotplug_event:733/connector_hotplug_event:747; drm_helper_hpd_irq_event:1082/drm_connector_helper_hpd_irq_event:1035; detect_from_ddc:1318.
- EDID→display_info: drm_edid_read include/drm/drm_edid.h:472 (impl drm_edid.c:2718); drm_edid_connector_update:7082; _connector_add_modes:7105; drm_add_edid_modes (legacy):7160; drm_edid_free:2569.
- Modeset helper: drm_helper_mode_fill_fb_struct drm_modeset_helper.c:83; mode_config_helper_suspend:194/_resume:240; move_panel_connectors_to_head:52.
- Writeback: drm_writeback_connector_init drm_writeback.c:171 / _with_encoder:321 / drmm_:391 / cleanup_job:489.
- Privacy screen: drm_privacy_screen_get drm_privacy_screen.c:116/_put:187/_register:391/_unregister:436/_register_notifier:281/lookup_add:56.
- Panic: drm_panic_register drm_panic.c:1028 / _unregister:1056.
- Driver init order: amdgpu — dm_early_init amdgpu_dm.c:5906 → amdgpu_dm_init:1872 → amdgpu_dm_mode_config_init:4918 → amdgpu_dm_initialize_drm_device:5442 [initialize_plane:5359+amdgpu_dm_plane_init amdgpu_dm_plane.c:1853; amdgpu_dm_crtc_init amdgpu_dm_crtc.c:722; amdgpu_dm_connector_init amdgpu_dm.c:9192; amdgpu_dm_encoder_init:9285]; props amdgpu_display_modeset_create_props amdgpu_display.c:1424, supported_domains:557. i915/xe — intel_display_driver_early_probe intel_display_driver.c:171 → probe_noirq:198 → probe_nogem:448 (mode_config+outputs) → probe:513 → register:549; intel_crtc_init intel_crtc.c:409; intel_connector_alloc intel_connector.c:104; DDI/eDP seam intel_ddi_init intel_ddi.c:5175; xe glue drivers/gpu/drm/xe/display/xe_display.c.

#### 3. Lifecycle & locking (anchors)
- mode_config locks (all in drm_mode_config, hdr:360): mutex = big modeset BKL (guards acquire_ctx); connection_mutex (drm_modeset_lock) = connector state + connector→encoder→CRTC routing; idr_mutex = object_idr+tile_idr; fb_lock (mutex) = fb_list/num_fb; blob_lock = property_blob_list + drm_file.blobs; connector_list_lock (spinlock) = connector_list/num_connector/free_list; panic_lock (raw_spinlock) = panic-safe HW/state access.
- Per-object modeset locks: drm_crtc.mutex, drm_plane.mutex (drm_modeset_lock, guard atomic @state). connector.mutex guards only registration_state; connector.eld_mutex guards eld.
- Bridge global list: bridge_lock (mutex, drm_bridge.c) guards drm_bridge.list.
- Refcounted lifetimes (via drm_mode_object.free_cb): drm_framebuffer, drm_connector, drm_property_blob (drm_*_get/_put). drm_bridge separately kref-refcounted (drm_bridge_get/put, new).
- devm/drmm-managed (auto-freed on drm_device release): drmm_mode_config_init, drmm_crtc/encoder/connector_init, drmm_universal_plane_alloc, drmm_kms_helper_poll_init — vs manual drm_*_cleanup for statically-embedded objects.
- Registration order: objects created + added to object_idr as "private" during driver init BEFORE drm_dev_register; drm_dev_register → drm_modeset_register_all → drm_{crtc,encoder,connector,plane}_register_all exposes to userspace (creates sysfs/kdev, sets registration_state=REGISTERED, num_connector++). Dynamic (MST) connectors added AFTER via drm_connector_dynamic_init/_dynamic_register (drm_connector.c:442/906), removed via unregister + drm_connector_put.

#### 4. Hard-coded limits (value · file:line)
- possible_crtcs mask: num_crtc >= 32 → -EINVAL, drm_crtc.c:267 ("crtc index used with 32bit bitmasks").
- possible_crtcs/plane mask: num_total_plane >= 32 → -EINVAL, drm_plane.c:379.
- possible_clones mask: num_encoder >= 32 → -EINVAL, drm_encoder.c:109.
- DRM_OBJECT_MAX_PROPERTY = 64 (props per object) — include/drm/drm_mode_object.h:63.
- DRM_PROP_NAME_LEN = 32 — include/uapi/drm/drm_mode.h:47.
- MAX_ELD_BYTES = 128 — include/drm/drm_connector.h:2225.
- EDID_LENGTH = 128 (per block) — include/drm/drm_edid.h:38; edid->extensions is u8 (≤255 blocks), valid_blocks recomputed drm_edid.c:2118.
- DRM_FORMAT_MAX_PLANES = 4u (fb pitches/offsets/obj arrays) — include/drm/drm_fourcc.h:32.
- BITMASK properties restricted to bits 0..63 (drm_property.h doc); blob property value stores a single 64-bit blob id.

#### 5. Version-specific facts (v7.0 vs older)
- drm_bridge is now refcounted: base changed to drm_private_obj + kref refcount (drm_bridge.h:1102/1131); drm_bridge_get/put (drm_bridge.c:292/308) with __drm_bridge_free freeing bridge->container; devm/drmm bridge-alloc pattern. Older kernels had no bridge refcount/get-put.
- Dynamic connectors: drm_connector_dynamic_init:442 + drm_connector_dynamic_register:906 for connectors hot-added after drm_dev_register (DP MST), teardown via drm_connector_put. Older code registered all connectors up-front only.
- drmm_connector_hdmi_init drm_connector.c:571 — newer HDMI-connector framework path.
- connector.eld now protected by dedicated eld_mutex (drm_connector.h:2229).
- display_info gained is_hdmi/has_audio/has_hdmi_infoframe + struct drm_hdmi_info hdmi (:754-800), superseding drm_detect_hdmi_monitor()/drm_detect_monitor_audio().
- Opaque `struct drm_edid` API (drm_edid_read:472/drm_edid_connector_update:7082/drm_edid_free:2569) supersedes raw `struct edid`+drm_get_edid/drm_add_edid_modes.
- Color pipeline: drm_plane_state.color_pipeline (drm_colorop) + mode_config.colorop_list/num_colorop + drm_plane_create_color_pipeline_property (drm_plane.c:1838) — newly added.
- drm_panic subsystem (drm_panic.c, drm_panic_register:1028) is recent; consumed by all three stacks (get_scanout_buffer).
- drm_crtc_create_sharpness_strength_property drm_crtc.c:961 — new CRTC property helper.

#### 6. Suggested page topics (beyond object-per-page)
- KMS object model: IDR + refcount + free_cb (drm_mode_object, drm_mode_object_find, DRM_OBJECT_MAX_PROPERTY).
- Object lifetime models: devm/drmm vs manual _cleanup vs free_cb refcount (drmm_* vs drm_*_cleanup) — recurring confusion point.
- Modeset locking model: mode_config locks + drm_modeset_lock + connection_mutex + connector_list_lock/iter.
- Standard/atomic property registry (drm_mode_config standard-prop pointers + drm_connector_create_standard_properties:1813).
- Plane composition properties: alpha/rotation/zpos/pixel_blend_mode (drm_blend.c).
- Legacy addfb vs addfb2 and FB refcount/handle semantics (drm_framebuffer.c internal_flags, filp_head).
- Connector probe/poll/hotplug state machine (drm_probe_helper.c poll_init/hpd_irq_event/hotplug_event; connector.polled/epoch_counter/registration_state).
- Dynamic connectors & MST hotplug registration (drm_connector_dynamic_*).
- EDID→display_info pipeline with opaque drm_edid (drm_edid_read/_connector_update).
- Helper callback-contract map (drm_modeset_helper_vtables.h) — the driver callback surface.
- Privacy screen on x86/ACPI (drm_privacy_screen*, drm_privacy_screen_x86.c ThinkPad HKEY.GSSS / Chrome GOOG0010).
- Writeback connectors — amdgpu-only in scope (see §7 negatives).
- drm_bridge model + why our x86 stacks bypass it (evidence in §7); refcount migration.
- DP/AUX seam at connector detect (connector helper detect_ctx → driver DPCD/AUX) — hard stop into DP knowledge base.
- drm_panic scanout integration (driver get_scanout_buffer, drm_panic_register).
- Driver wrapper/subclass pattern (amdgpu_*/dm_* and intel_* embedding drm base objects).

#### 7. Tracepoints
- Generic KMS core (mode_config/object/property/framebuffer/plane/crtc/encoder/connector/bridge/probe_helper/edid): NONE. The only generic drm tracepoints are vblank: drm_vblank_event drm_trace.h:15, drm_vblank_event_queued:35, drm_vblank_event_delivered:52 — no object-creation/probe/hotplug tracepoints anywhere in this area.
- amdgpu (amdgpu_dm_trace.h): atomic-path only — amdgpu_dm_connector_atomic_check:104, amdgpu_dm_crtc_atomic_check:161, amdgpu_dm_plane_atomic_check:309, amdgpu_dm_atomic_commit_tail_begin/finish:349/353, amdgpu_dm_atomic_check_begin/finish:357/361, plus DC reg/clock/brightness events. No object-init tracepoints.
- i915/xe (intel_display_trace.h, shared with xe): pipe/plane/crtc runtime events — intel_pipe_enable:69/intel_pipe_disable:98, intel_crtc_flip_done:128, intel_plane_update_arm/noarm/disable:410/443/476, intel_pipe_update_start/end:730/786, intel_fbc_*, intel_crtc_vblank_work_*. No connector/encoder/object-creation tracepoints.

#### Negative findings (evidence)
- drm_bridge is NOT used by amdgpu_dm, i915/display, or xe/display on x86 (zero drm_bridge_attach/devm_drm_bridge_alloc/drm_bridge_connector references in those trees, DSI excluded) — bridge model is out-of-band for our two stacks; document at seam only.
- Writeback connectors: amdgpu ONLY (amdgpu_dm_wb.c) — i915/xe expose none (no drm_writeback references).
- drm_panic get_scanout_buffer implemented by all three (amdgpu_dm_plane.c, i915 intel_plane.c, xe display/xe_panic.c).
- Privacy screen is x86/ACPI-relevant (drm_privacy_screen_x86.c: ThinkPad ACPI + ChromeOS GOOG0010 lookups).
### Area C: ioctl & atomic uapi — COMPLETE (recorded 2026-07-12)

#### 1. Core structs (field groups · role · file:line)
- `drm_ioctl_desc` — `include/drm/drm_ioctl.h:134`; {cmd, flags(enum drm_ioctl_flags), func(drm_ioctl_t*), name}. One table entry per ioctl.
- `enum drm_ioctl_flags` — `include/drm/drm_ioctl.h:80`; DRM_AUTH=BIT(0), DRM_MASTER=BIT(1), DRM_ROOT_ONLY=BIT(2), DRM_RENDER_ALLOW=BIT(5). (DRM_MAJOR 226 @:72)
- `drm_file` — `include/drm/drm_file.h:165`; caps bools (authenticated, universal_planes, atomic, aspect_ratio_allowed, writeback_connectors, plane_color_pipeline, was_master/is_master, supports_virtualized_cursor_plane); master ptr+master_lookup_lock; idr object_idr; fbs/blobs lists; event_wait/pending_event_list/event_list/event_space/event_read_lock; client_id/client_name/debugfs_client.
- `drm_master` — `include/drm/drm_auth.h:47`; {kref, dev, unique, magic_map(idr), lessor, lessee_id, lessee_list, lessees, leases(idr), lessee_idr} — lease tree.
- `drm_pending_event` — `include/drm/drm_file.h:96`; {completion, completion_release, event(drm_event*), fence(dma_fence*), file_priv, link, pending_link} — generic completion/fence/event delivery.
- `drm_event` (uapi) — `include/uapi/drm/drm.h:1391`; {type, length} header for FD reads.
- `drm_modeset_acquire_ctx` — `include/drm/drm_modeset_lock.h:46`; {ww_ctx, contended, stack_depot, locked(list), trylock_only, interruptible} — ww-mutex EDEADLK context.
- `drm_atomic_state` — `include/drm/drm_atomic.h:467`; {kref, dev, bits allow_modeset/legacy_cursor_update/async_update/duplicated/checked/plane_color_pipeline; colorops/planes/crtcs/connectors/private_objs arrays; num_connector/num_private_objs; acquire_ctx; fake_commit; commit_work}.
- `__drm_crtcs_state` — `include/drm/drm_atomic.h:186`; {ptr, state_to_destroy, old_state, new_state, commit(drm_crtc_commit*), out_fence_ptr, last_vblank_count}. `__drm_planes_state`@:165 (no commit/out_fence).
- `drm_crtc_commit` — `include/drm/drm_atomic.h:72`; {crtc, kref, completions flip_done/hw_done/cleanup_done, commit_entry, event, abort_completion}. cleanup_done is terminal; flip_done↔hw_done order is driver-specific.
- `drm_private_obj` — `include/drm/drm_atomic.h:340` {dev, head, lock, state, funcs}; `drm_private_state`@:390 {state(backptr), obj}. Lifetime tied to drm_device; ordering warning re non-blocking commits in doc.
- uapi: `drm_mode_atomic` — `include/uapi/drm/drm_mode.h:1342` {flags, count_objs, objs_ptr, count_props_ptr, props_ptr, prop_values_ptr, reserved, user_data}. `drm_mode_fb_cmd2`@:704 {fb_id,w,h,pixel_format,flags,handles[4],pitches[4],offsets[4],modifier[4]}. (drm_mode_crtc/drm_mode_set_plane/drm_mode_cursor2 also in drm_mode.h.)

#### 2. API families (file:line · role)
- Dispatch: `drm_ioctl` `drm_ioctl.c:821` (nr→core `drm_ioctls[]` `:632` via DRM_IOCTL_DEF `:623`, or driver table; copy_in/out; `stack_kdata[128]`) → `drm_ioctl_kernel` `:787` (drm_file_update_pid, permit, func).
- Permission: `drm_ioctl_permit` `:599` (ROOT_ONLY→CAP_SYS_ADMIN, AUTH→authenticated/render, MASTER→drm_is_current_master, render-node gating). Caps: `drm_getcap` `:234`, `drm_setclientcap` `:317` (STEREO_3D/UNIVERSAL_PLANES/ATOMIC/ASPECT_RATIO/WRITEBACK_CONNECTORS/CURSOR_PLANE_HOTSPOT/PLANE_COLOR_PIPELINE).
- State get/add (`drm_atomic.c`): alloc `:171`/init `:126`/default_release `:106`/default_clear `:200`/clear `:306`; get_crtc `:365`, get_plane `:546`, get_connector `:1273`, get_colorop `:610`, get_private_obj `:977`; add_affected_connectors `:1502`, add_affected_planes `:1566`, add_affected_colorops `:1611`; check_only `:1647` (walks then `config->funcs->atomic_check` `:1698`); commit `:1760`, nonblocking_commit `:1793` (both call check then `config->funcs->atomic_commit`).
- Atomic uapi (`drm_atomic_uapi.c`): `drm_mode_atomic_ioctl` `:1559`; `drm_atomic_set_property` `:1170` routes on obj->type CONNECTOR/CRTC/PLANE/COLOROP `:1184-`; fences `setup_out_fence` `:1355`, `prepare_signaling` `:1372`, `complete_signaling` `:1497`; async no-op guard `drm_atomic_check_prop_changes` `:1157`.
- Atomic-helper check/commit phases (`drm_atomic_helper.c`): `drm_atomic_helper_check` `:1107` (→check_modeset+check_planes); prepare_planes `:2814`; swap_state `:3252`; commit_modeset_disables `:1566`, commit_planes `:2972`, commit_modeset_enables `:1759`, cleanup_planes `:3202`; commit_tail(static) `:2034`, commit_work(static) `:2087`, drm_atomic_helper_commit_tail `:1983`; commit `:2245`; setup_commit `:2511`; wait_for_fences `:1834`, wait_for_vblanks `:1883`, wait_for_flip_done `:1944`, wait_for_dependencies `:2636`; commit_hw_done `:2729`, commit_cleanup_done `:2774`, fake_vblank `:2691`.
- Default state ops (`drm_atomic_state_helper.c`): crtc reset/dup/destroy `:114/:171/:230`, plane `:330/:373/:419`, connector `:474/:661/:708` (+`__`-prefixed inner variants `:74/:436/:637`).
- Event send/consume (`drm_file.c`): reserve_init_locked `:661`/reserve_init `:702`, cancel_free `:727`, send_helper(static) `:746`, send_locked `:814`, send `:835`; consume via drm_read `:540`, drm_poll `:624`.

#### 3. Lifecycle & locking (anchors)
- EDEADLK protocol (`drm_modeset_lock.c`): acquire_init `:248` → lock `:394` returns -EDEADLK on contention → caller `drm_atomic_state_clear` + `drm_modeset_backoff` `:348` (drops all, slow-locks contended) → retry; drop_locks `:276`, acquire_fini, lock_all_ctx `:451`. Canonical in-tree loop: `drm_mode_atomic_ioctl` retry: label + `out:` backoff `drm_atomic_uapi.c:1626/1724-1729`.
- Atomic state lifetime: alloc (`drm_atomic.c:171`) → property decode into per-obj new_state → check_only (`:1647`) sets `checked`, forbids further mutation → helper swap_state (`:3252`, old↔new, `state_to_destroy` flips) → commit_tail phases → cleanup_planes → put(kref). state_clear frees to pre-check.
- Commit ordering/stall (drm_crtc_commit refcounts): setup_commit `:2511` inits completions + takes extra ref for `state.event` (abort_completion); `stall_checks` `:2375` throttles to ≤1 outstanding non-block commit (waits prev-prev cleanup_done); wait_for_dependencies `:2636` blocks on old_state->commit of crtc/connector/plane; hw_done→(flip_done)→cleanup_done terminal; non-block work queued `system_unbound_wq` `:2310`.
- drm_file open/release (`drm_file.c`): open `:369`→file_alloc `:132` (sets `event_space=4096` `:158`, `drm_master_open` if primary); release `:427`→ drain events → file_free `:233` (postclose, master_release, free fbs/blobs). read serialized by event_read_lock; pending vs ready event lists split.
- Master/auth (`drm_auth.c`): drm_is_current_master `:82`; SET/DROP via `drm_setmaster_ioctl` `:245`/`drm_dropmaster_ioctl` `:288` (table flags 0 — self-checks + ROOT override); new_set_master `:162`, master_create `:131`, master_open `:317`, master_release `:337`; magic auth getmagic `:94`/authmagic `:113`. Lease filtering (`drm_lease.c`): `_drm_lease_held` `:109`/`drm_lease_held` `:126`, `drm_lease_filter_crtcs` `:154`, lease_owner `:74`, create `:207`/destroy `:266`; ioctls create `:475`/list/get `:636`/revoke `:694`.

#### 4. Hard-coded limits (value · file:line)
- Core ioctl table size = `ARRAY_SIZE(drm_ioctls)` → `DRM_CORE_IOCTL_COUNT` `drm_ioctl.c:737` (57 entries, `:632-735`); driver ioctls bounded by `driver->num_ioctls` in [DRM_COMMAND_BASE,DRM_COMMAND_END).
- ioctl on-stack copy buffer `stack_kdata[128]` `drm_ioctl.c:830` (larger → kmalloc).
- Per-file event space 4096 bytes `drm_file.c:158` (checked `:666`, EBUSY when exhausted).
- flip_done wait 10*HZ `drm_atomic_helper.c:1959`; wait_for_vblanks per-CRTC 100ms `:1919`; stall_checks cleanup_done 10*HZ `:2414`.
- MODE_ATOMIC: no hard cap on count_objs/count_props (bounded by user counts + per-obj prop lookup ENOENT); flags mask `DRM_MODE_ATOMIC_FLAGS` `drm_mode.h:1335` (TEST_ONLY 0x100, NONBLOCK 0x200, ALLOW_MODESET 0x400, PAGE_FLIP_EVENT 0x01, PAGE_FLIP_ASYNC 0x02); setclientcap ATOMIC rejects value>2 `:317`.

#### 5. Version-specific facts at v7.0
- Plane color pipeline (new): cap `DRM_CLIENT_CAP_PLANE_COLOR_PIPELINE` (setclientcap `:317`), `drm_file.plane_color_pipeline`, `drm_atomic_state.plane_color_pipeline`, `DRM_MODE_OBJECT_COLOROP` routing in `drm_atomic_set_property:1273`, `drm_atomic_get_colorop_state` (`drm_atomic.c:610`), `__drm_colorops_state`/`colorops` array in state; when set, helpers ignore legacy COLOR_RANGE/COLOR_ENCODING.
- setclientcap ATOMIC value 2 accepted (>2 rejected); still guards broken 'X'/modesetting-DDX (`:317`).
- Newer ioctls present in table: `DRM_IOCTL_MODE_CLOSEFB` (`:692`, drm_mode_closefb_ioctl), `DRM_IOCTL_GEM_CHANGE_HANDLE` (`:663`), `DRM_IOCTL_SET_CLIENT_NAME` (`:670`, DRM_RENDER_ALLOW), `SYNCOBJ_EVENTFD` (`:719`).
- Atomic async flip: `DRM_MODE_PAGE_FLIP_ASYNC` in atomic path gated by `mode_config.async_page_flip`; `set_async_flip` + no-op/flip-only prop validation via `drm_atomic_check_prop_changes` (`drm_atomic_uapi.c:1157`, async branch `:1195-1265`).
- fdinfo/debugfs per-client: `drm_file.client_id/client_name/client_name_lock/debugfs_client` (drm_file.h:165) with SET_CLIENT_NAME ioctl.

#### 6. Suggested page topics (attack by anchor · thin flags)
- ioctl-dispatch — `drm_ioctl`/`drm_ioctl_kernel`/`drm_ioctl_permit`/`drm_ioctls[]`/DRM_IOCTL_DEF + flags enum. Solid.
- client-caps — getcap/setclientcap + DRM_CLIENT_CAP_* + drm_file bools. Thin — merge into ioctl-dispatch.
- drm_file & events — file_alloc/free/open/release, read/poll, pending/ready event lists, drm_send_event*/event_reserve_init, drm_pending_event/drm_event, event_space. Solid.
- master-auth-lease — drm_master, SET/DROP_MASTER, magic, drm_is_current_master; lease tree + filter_crtcs + lease ioctls. Solid (could split lease if long).
- modeset-locking / EDEADLK — drm_modeset_acquire_ctx, backoff/lock_all_ctx, ww-mutex dance. Solid but compact — pairs well with atomic-state.
- atomic-state-objects — drm_atomic_state + `__drm_*_state` arrays, get_/add_affected_, private_objs, alloc/clear lifetime. Solid.
- atomic-ioctl-decode — drm_mode_atomic_ioctl, set_property routing (incl COLOROP), OUT_FENCE/IN_FENCE, TEST_ONLY/NONBLOCK/EVENT flags. Solid.
- atomic-helper-commit-machinery — check→swap→commit_tail phases, setup_commit, drm_crtc_commit refcounts, stall/wait_for_dependencies, non-block worker. Solid (biggest).
- default-state-helpers — reset/duplicate/destroy. Thin — merge into atomic-state-objects.
- legacy-over-atomic — setcrtc/setplane/cursor/page_flip/DIRTYFB over atomic. Solid.
- ADDFB2 path — framebuffer_check/internal_framebuffer_create/addfb2/getfb2/rmfb. Solid.
- dumb-buffers — create_dumb + driver dumb_create. Thin — merge with ADDFB2 or driver page.
- driver-commit-impls — amdgpu (helper_commit + amdgpu_dm_atomic_commit_tail) vs i915/xe (own intel_atomic_commit). Solid (contrast page).

#### 7. Tracepoints/trace events
- Generic core: NONE. No `trace_*` in drm_ioctl.c, drm_file.c, drm_atomic.c, drm_atomic_uapi.c, drm_atomic_helper.c, drm_atomic_state_helper.c — they use `drm_dbg_atomic`/`drm_dbg_core` printk-style debug only.
- amdgpu_dm (header `amdgpu_dm_trace.h`, TRACE_EVENTs @:104/:161/:317/:361…): `trace_amdgpu_dm_atomic_commit_tail_begin` `amdgpu_dm.c:10883` / `_finish` `:11164`; `trace_amdgpu_dm_atomic_check_begin` `:12497` / `_finish` `:12972,:12984`; `trace_amdgpu_dm_connector_atomic_check` `:8312`.
- i915/xe display (`intel_display_trace.h`): commit_tail itself untraced; flip/pipe events fired from adjacent paths — `trace_intel_pipe_update_start/vblank_evaded/end` `intel_crtc.c:594/:604/:696`, `trace_intel_crtc_flip_done` `intel_display_irq.c:470`, `trace_intel_plane_async_flip` `intel_plane.c:879`. xe reuses shared i915 display; `xe/display/xe_display.c` has no `trace_*`.

#### Driver landing anchors
- amdgpu — fb_create `amdgpu_display.c:1297` (amdgpu_mode_funcs `:1344`), atomic_check `amdgpu_dm.c:12476` / commit_tail `:10866`, mode_config_helper wiring `:3738-3743` (`.atomic_commit=drm_atomic_helper_commit`), dumb `amdgpu_gem.c:1252` (wired `amdgpu_drv.c:3101`).
- i915/xe — fb_create `intel_fb.c:2341`, mode funcs `intel_display_driver.c:99`, own `intel_atomic_commit` `intel_display.c:7701` (setup_commit `:7673`, swap_state `:7688`, per-display `wq.modeset`/`wq.flip` `:7760/:7762`), commit_tail `:7414`, commit_work `:7648`; dumb i915 `i915_gem_dumb_create` (wired `i915_driver.c:1871`), xe `xe_bo_dumb_create` `xe_bo.c:3627` (wired `xe_device.c:402`).
### Area D: display timing, vblank & sync — COMPLETE (recorded 2026-07-12)

#### 1. Core structs (field groups · role · file:line)
- drm_display_mode `include/drm/drm_modes.h:252` — logical timings (clock,hdisplay/hsync_start/hsync_end/htotal + hskew, vertical twins, vscan), `flags` (DRM_MODE_FLAG_*), hw-adjusted copies (crtc_clock, crtc_h*/crtc_v* incl. crtc_hblank_start/end), width_mm/height_mm, type, status, picture_aspect_ratio, name[], head.
- drm_vblank_crtc `include/drm/drm_vblank.h:139` — per-CRTC vblank state: `queue`, `disable_timer`, `seqlock`, `count`(atomic64), `time`, `refcount`(atomic), `last`/`max_vblank_count`/`inmodeset` (wraparound), `pipe`, `framedur_ns`/`linedur_ns`, cached `hwmode`, `config`(drm_vblank_crtc_config), `enabled`, `worker`(kthread), `pending_work`, `work_wait_queue`, `vblank_timer`.
- drm_vblank_crtc_config `include/drm/drm_vblank.h:85` — `offdelay_ms`, `disable_immediate`.
- drm_pending_vblank_event `include/drm/drm_vblank.h:43` — `base`(drm_pending_event), `pipe`, `sequence`, union event{base, vbl(drm_event_vblank), seq(drm_event_crtc_sequence)}.
- drm_vblank_work `include/drm/drm_vblank_work.h:22` — `base`(kthread_work), `vblank`, target `count`, `cancelling`, `node`.
- dma_fence `include/linux/dma-fence.h:67` — `lock`(spinlock_t* — pointer), `ops`, union{cb_list / timestamp / rcu}, `context`, `seqno`, `flags`(DMA_FENCE_FLAG_*), `refcount`(kref), `error`.
- dma_fence_ops `include/linux/dma-fence.h:128` — get_driver_name/get_timeline_name(mandatory), enable_signaling, signaled, wait, release, set_deadline.
- dma_fence_chain `include/linux/dma-fence-chain.h:25` — `base`, `prev`(rcu), `prev_seqno`, `fence`, union{cb,work}, `lock`.
- dma_fence_array `include/linux/dma-fence-array.h:38` — `base`, `lock`, `num_fences`, `num_pending`(atomic), `**fences`, `work`, `callbacks[] __counted_by`.
- dma_resv `include/linux/dma-resv.h:155` — `lock`(ww_mutex), `fences`(dma_resv_list rcu). Usage classes enum dma_resv_usage `include/linux/dma-resv.h:71` (KERNEL<WRITE<READ<BOOKKEEP).
- drm_syncobj `include/drm/drm_syncobj.h:39` — `refcount`(kref), `fence`(dma_fence rcu), `cb_list`, `ev_fd_list`, `lock`(spinlock), `file`.
- amdgpu_fence `drivers/gpu/drm/amd/amdgpu/amdgpu_ring.h:142` — `base`(dma_fence), `ring`, start_timestamp, wptr/context, reemitted, fence_wptr_start/end (ring/reset fencing).

#### 2. API families (file:line · role)
- Mode timing math (`drivers/gpu/drm/drm_modes.c`): drm_mode_vrefresh:1287; drm_mode_set_crtcinfo:1348 (fill crtc_* adjusted); drm_mode_set_name:1270; drm_mode_copy:1420/drm_mode_init:1439/drm_mode_duplicate:1457/drm_mode_destroy:93; drm_mode_match:1531/equal:1575/equal_no_clocks:1598; drm_mode_prune_invalid:1806; drm_mode_convert_to_umode:2582 / drm_mode_convert_umode:2637 (uapi drm_mode_modeinfo↔kernel); drm_mode_debug_printmodeline:58.
- Vblank get/put/on/off (`drivers/gpu/drm/drm_vblank.c`): drm_vblank_init:539; drm_crtc_vblank_get:1248/put:1285; drm_crtc_vblank_on:1528 / on_config:1482 / off:1339 / reset:1418; internal drm_vblank_enable:1173, drm_vblank_disable_and_save:461, vblank_disable_fn:497.
- Sequence/count: drm_crtc_vblank_count:936, drm_crtc_vblank_count_and_time:996, drm_crtc_accurate_vblank_count:420, drm_update_vblank_count:295, store_vblank:191.
- Event arm/send: drm_crtc_arm_vblank_event:1113, drm_crtc_send_vblank_event:1138; handle drm_crtc_handle_vblank:1992 (legacy drm_handle_vblank:1918).
- Timestamping: drm_calc_timestamping_constants:626, drm_crtc_vblank_helper_get_vblank_timestamp[_internal]:851/708, drm_crtc_vblank_get_vblank_timeout:2285.
- Ioctls: drm_wait_vblank_ioctl:1734, drm_crtc_get_sequence_ioctl:2006, drm_crtc_queue_sequence_ioctl:2063.
- Vblank-work (`drivers/gpu/drm/drm_vblank_work.c`): schedule:111, cancel_sync:187, flush:223, flush_all:244, init:267, worker_init:276; drm_handle_vblank_works:48, drm_vblank_cancel_pending_works:72.
- Fence init/signal/wait/callback (`drivers/dma-buf/dma-fence.c`): __dma_fence_init:1045 / dma_fence_init:1079 / dma_fence_init64:1090s (decl dma-fence.h:259); signal:486/signal_locked:426/signal_timestamp:400; wait_timeout:523/default_wait:800/wait_any_timeout:887 (inline dma_fence_wait `include/linux/dma-fence.h:653`); add_callback:682; enable_sw_signaling:650; release:561/free:612; context_alloc:185; get_stub:143/allocate_private_stub:155; set_deadline:1008.
- Fence chain/array/unwrap: dma_fence_chain_init `dma-fence-chain.c:240`/walk:39/find_seqno:90; dma_fence_array_create `dma-fence-array.c:252`/alloc:178/first:296/next:314; __dma_fence_unwrap_merge `dma-fence-unwrap.c:118`/unwrap_first:34/next:49.
- resv lock/add/iterate (`drivers/dma-buf/dma-resv.c`): init:138/fini:150; reserve_fences:182; add_fence:287; replace_fences:343; iter_first:471/iter_next:493; copy_fences:521; get_singleton:627; wait_timeout:678; set_deadline:711; test_signaled:738. Locks inline `include/linux/dma-resv.h`: dma_resv_lock:342/interruptible:369/slow:386/trylock:422/unlock:461.
- syncobj find/replace/wait (`drivers/gpu/drm/drm_syncobj.c`): find:248; add_point:333; replace_fence:372; find_fence:436; create:554/get_fd:662; ioctls create:822/destroy:839/handle_to_fd:854/fd_to_handle:886/transfer:982/wait:1321/timeline_wait:1364/eventfd:1460/query:1652; add_eventfd:315.
- sync_file (`drivers/dma-buf/sync_file.c`): create:65/get_fence(via)/merge:165/poll:197/ioctl:382/release:185.
- VRR enable paths: props — drm_connector_attach_vrr_capable_property `drm_connector.c:2386` (`vrr_capable_property` `include/drm/drm_connector.h:2100`); crtc `vrr_enabled` `include/drm/drm_crtc.h:300`, atomic set/get `drm_atomic_uapi.c:413/496`, `prop_vrr_enabled` `include/drm/drm_mode_config.h:699`. i915 (`display/intel_vrr.c`): is_capable:33/is_in_range:69, set_transcoder_timings:592, send_push:691, enable:922/disable:936, get_config:1010. amdgpu freesync (`modules/freesync/freesync.c`): build_vrr_params:977, handle_preflip:1129, handle_v_update:1167, build_vrr_infopacket:941.
- PSR/replay gating: i915 (`display/intel_psr.c`) compute_config:1850, activate:1953, pre_plane_update:3088/post_plane_update:3153 (gate around plane commit), invalidate:3551/flush:3661, disable:2384/pause:2413/resume:2444. amdgpu (`amdgpu_dm_psr.c`) enable:148/disable:207/disable_all:222/is_active_allowed:235; replay (`amdgpu_dm_replay.c`) enable:153/disable:187/disable_all:212.

#### 3. Lifecycle & locking (anchors)
- Vblank refcount+disable timer: `drm_crtc_vblank_get`→enable at first ref; `put` arms `disable_timer` (`drm_vblank.c:1285`); timer fires `vblank_disable_fn:497`→`drm_vblank_disable_and_save:461`; immediate-disable path in `put`:1270. `count`/`time` protected by per-CRTC `seqlock` (readers use `drm_vblank_count_and_time:956`); `refcount` atomic; `last`/`inmodeset` under `drm_device.vbl_lock`.
- Event locking: pending events + send under `drm_device.event_lock` (see amdgpu `amdgpu_dm_crtc_handle_vblank` spin_lock_irqsave(&dev->event_lock)).
- Fence refcount+RCU: `refcount`(kref)→`dma_fence_release:561` via `kfree_rcu`(rcu union member); flags manipulated via atomic bitops; `cb_list` valid only until SIGNALED bit set, requires a held ref (not just rcu_read_lock) — documented in struct.
- resv held rules: update side under `dma_resv_lock` (ww_mutex); `add_fence`/`replace_fences` require lock held + prior `reserve_fences`; lockless readers use `dma_resv_iter_*` under RCU (rcu_read_lock, retry on seq change).
- syncobj: `->lock`(spinlock) protects `cb_list`+`ev_fd_list` and write-locks `fence`; readers use `drm_syncobj_fence_get` (RCU deref of `fence`).

#### 4. Hard-coded limits (value · file:line)
- Vblank auto-disable delay: `drm_vblank_offdelay = 5000` ms `drm_vblank.c:171` (module param `vblankoffdelay`, 0=never, <0=immediate:173).
- Timestamp retry cap: `DRM_TIMESTAMP_MAXRETRIES 3` `drm_vblank.c:158`; timestamp precision param `timestamp_precision_usec` `drm_vblank.c:174`.
- syncobj submit-wait default: `DRM_SYNCOBJ_WAIT_FOR_SUBMIT_TIMEOUT 5000000000ULL` (5 s) `drm_syncobj.c:420`.
- Fence blocking-wait default: `MAX_SCHEDULE_TIMEOUT` in `dma_fence_wait` inline `include/linux/dma-fence.h:661`.
- syncobj wait: no fixed stack-batch; wait entries via `kzalloc_objs`/`kmalloc_array(count,...)` `drm_syncobj.c:1052/1065`.

#### 5. Version-specific facts at v7.0
- dma_fence.lock is `spinlock_t *` (pointer) and struct field order is lock/ops-first with `refcount` late (`include/linux/dma-fence.h:67`) — differs from older embedded-order layouts.
- `dma_fence_init64()` added alongside `dma_fence_init()` (`dma-fence.c:1079/1090s`, decl `:259`) — 64-bit-seqno init variant, new vs older kernels.
- dma_fence tracepoints use helpers `dma_fence_driver_name()`/`dma_fence_timeline_name()` (`include/trace/events/dma_fence.h:19-20`) instead of raw `fence->ops->get_*` (the older `_unsignaled` class still uses raw ops:49-50).
- dma_resv_usage enum era present (KERNEL/WRITE/READ/BOOKKEEP, `include/linux/dma-resv.h:71`) — the modern usage-class API (post shared/exclusive split).
- Vblank config is per-CRTC via `drm_vblank_crtc_config` + `drm_crtc_vblank_on_config()` (`drm_vblank.c:1482`) — newer than the flat offdelay-only model.
- syncobj eventfd ioctl present (`drm_syncobj_eventfd_ioctl` `drm_syncobj.c:1460`, `syncobj_eventfd_entry` `:226`).
- amdgpu `amdgpu_fence` carries reset/reemit fields (wptr/reemitted/fence_wptr_start-end) — recent GPU-reset-robust fencing.
- `kzalloc_objs()` helper used in syncobj wait (`:1065`) — recent allocation helper.

#### 6. Suggested page topics (anchor justification; merge/gap flags)
- display-mode-timing — drm_display_mode + drm_modes.c math (set_crtcinfo/vrefresh/convert). Solid standalone.
- vblank-machinery — drm_vblank_crtc, get/put/on/off, count/timestamp, WAIT_VBLANK+SEQUENCE ioctls, drm_vblank.c. Solid standalone.
- vblank-work — drm_vblank_work + drm_vblank_work.c (6 fns). Thin-ish; keep but could annex to vblank-machinery.
- VRR/FreeSync — props (vrr_capable/vrr_enabled) + intel_vrr.c + amdgpu freesync module. Solid; cross-driver.
- PSR/panel-replay (eDP) — intel_psr.c + amdgpu_dm_psr.c/replay.c; framed as vblank/frame-update gating. Solid.
- dma-fence — dma-fence.c + ops + chain/array/unwrap + tracepoints. Solid, large.
- dma-resv — split recommended: distinct lock model + usage enum (dma-resv.c/h). Solid standalone.
- sync_file — sync_file.c only (~6 fns). THIN → merge into drm-syncobj or dma-fence (uapi fence FD).
- drm-syncobj — drm_syncobj.c (binary/timeline, chains, eventfd, ioctls). Solid.
- driver-fence-producers — amdgpu_fence.c(emit:112) / xe_hw_fence.c(init:233) / i915_request.c(add:1845, breadcrumbs via __i915_request_submit:606). One-line anchors; keep as single "who signals" page.
- Gaps to add: fence-consumption-in-display (drm_atomic_helper_wait_for_fences `drm_atomic_helper.c:1834`; plane fence set at amdgpu `amdgpu_dm_plane_helper_prepare_fb` `amdgpu_dm_plane.c:925`→drm_gem_plane_helper_prepare_fb:981, i915 `intel_prepare_plane_fb` `intel_plane.c:1197`) — worth a short page or a section under dma-fence.
- Descope note: generic `drm_self_refresh_helper.c` is used only by msm/rockchip (DT drivers), NOT amdgpu/i915/xe (`grep -rl` hits only drm_atomic_helper.c + msm/rockchip) — DT-oriented, descope for this ACPI/amd/i915/xe campaign.

#### 7. Tracepoints & trace events (file:line)
- Generic vblank `drivers/gpu/drm/drm_trace.h`: `drm_vblank_event`:15, `drm_vblank_event_queued`:35, `drm_vblank_event_delivered`:52.
- dma_fence `include/trace/events/dma_fence.h`: classes `dma_fence`:12 / `dma_fence_unsignaled`:42; events `dma_fence_emit`:67, `dma_fence_init`:74, `dma_fence_destroy`:81, `dma_fence_enable_signal`:88, `dma_fence_signaled`:95, `dma_fence_wait_start`:102, `dma_fence_wait_end`:109.
- i915/xe display `drivers/gpu/drm/i915/display/intel_display_trace.h`: `intel_crtc_flip_done`:128, `intel_plane_async_flip`:383, `intel_crtc_vblank_work_start`:684 / `_end`:707, `intel_pipe_update_vblank_evaded`:758, `intel_frontbuffer_invalidate`:809 / `_flush`:830. No dedicated intel_psr tracepoint (grep empty in intel_psr.c; PSR observability via frontbuffer events + debugfs).
- amdgpu_dm `drivers/gpu/drm/amd/display/amdgpu_dm/amdgpu_dm_trace.h`: `amdgpu_dc_rreg`:65/`_wreg`:69, `amdgpu_dm_atomic_commit_tail_begin`:349/`_finish`:353, `amdgpu_dm_atomic_check_begin`:357/`_finish`:361, `amdgpu_refresh_rate_track`:624 (VRR), `amdgpu_dmub_trace_high_irq`:603, `amdgpu_dm_dc_pipe_state`:384.
- xe: no xe-display-specific trace header; xe uses shared i915 display trace + `drivers/gpu/drm/xe/xe_trace.h` (engine/fence, not display).

#### Driver vblank glue (confirmed anchors)
- amdgpu non-VRR `dm_crtc_high_irq` `amdgpu_dm.c:645`→`amdgpu_dm_crtc_handle_vblank` `amdgpu_dm_crtc.c:41`→`drm_crtc_handle_vblank`:47; VRR path via `dm_vupdate_high_irq` `amdgpu_dm.c:574`→handle_vblank:617; enable/disable `amdgpu_dm_crtc_enable_vblank`:415/`disable`:420/`set_vblank`:290; scanout `amdgpu_display_get_crtc_scanoutpos` `amdgpu_display.c:1607`.
- i915/xe: `intel_handle_vblank` `intel_display_irq.c:146`→drm_crtc_handle_vblank:150 (dispatched for xe via `xe_display_irq_handler` `xe/display/xe_display.c:204`); scanline `__intel_get_crtc_scanline` `intel_vblank.c:244`, ts `intel_crtc_get_vblank_timestamp`:457; on/off `intel_crtc_vblank_on/off` `intel_crtc.c:128/147`.
### Area E: GEM + TTM buffer objects & dma-buf sharing — COMPLETE (recorded 2026-07-12)

#### 1. Core structs (field groups · role · file:line — all confirmed on disk)
- drm_gem_object — `include/drm/drm_gem.h:283` — refcount(kref) + handle_count(obj vs handle refs), dev, filp(shmem backing), vma_node(mmap fake-offset), size/name(flink), dma_buf + import_attach, resv/_resv(==&_resv except imports), gpuva(GPUVM), funcs, lru_node/lru. The generic BO base.
- drm_gem_object_funcs — `drm_gem.h:75` — free(mandatory), open/close(handle lifecycle), export, pin/unpin(for dma-buf), get_sg_table, vmap/vunmap, mmap, evict, status/rss, vm_ops. Per-object function pointer struct (supersedes drm_driver cbs).
- drm_gem_lru — `drm_gem.h:249` — mutex*, count(pages), list. Shrinker helper.
- drm_vma_offset_node — `include/drm/drm_vma_manager.h:52` — vm_lock, vm_node(drm_mm_node), vm_files(rb_root of allowed drm_files), driver_private. drm_vma_offset_manager — `:59` — vm_lock, vm_addr_space_mm(drm_mm).
- dma_buf — `include/linux/dma-buf.h:294` — size, file(refcount), attachments list, ops, vmapping_counter/vmap_ptr, exp_name/name, owner, priv, resv, poll. dma_buf_ops — `:37` — attach/detach, pin/unpin, map/unmap_dma_buf(mandatory), release(mandatory), begin/end_cpu_access, mmap, vmap/vunmap. dma_buf_attachment — `:489` — dmabuf, dev, node, peer2peer, importer_ops/priv, priv.
- ttm_device — `include/drm/ttm/ttm_device.h:216` — device_list, alloc_flags(TTM_ALLOCATION_*), funcs, sysman, man_drv[TTM_NUM_MEM_TYPES], vma_manager, pool, lru_lock, unevictable, dev_mapping, wq(delayed delete). ttm_device_funcs — `:62` — ttm_tt_create/populate/unpopulate/destroy, eviction_valuable, evict_flags, move, delete_mem_notify, swap_notify, io_mem_reserve/free/pfn, access_memory, release_notify. The driver contract.
- ttm_buffer_object — `include/drm/ttm/ttm_bo.h:101` — base(drm_gem_object superclass), bdev, type(enum ttm_bo_type `:67` device/kernel/sg), page_alignment, destroy, kref (own refcount, separate from base gem), resource, ttm, deleted, bulk_move, priority, pin_count, delayed_delete(work_struct), sg.
- ttm_resource — `include/drm/ttm/ttm_resource.h:263` — start, size, mem_type, placement, bus, bo(weak ref), css(dmem_cgroup_pool_state), lru(ttm_lru_item). ttm_resource_manager — `:199` — use_type/use_tt, bdev, size, func, eviction_lock + eviction_fences[TTM_NUM_MOVE_FENCES], lru[TTM_MAX_BO_PRIORITY], usage, cg(dmem_cgroup_region). ttm_resource_manager_func — `:100` — alloc/free/intersects/compatible/debug. ttm_lru_bulk_move — `:316` — pos[TTM_NUM_MEM_TYPES][TTM_MAX_BO_PRIORITY], cursor_list.
- ttm_place — `include/drm/ttm/ttm_placement.h:83` — fpfn, lpfn, mem_type, flags. ttm_placement — `:98` — num_placement, placement*.
- ttm_tt — `include/drm/ttm/ttm_tt.h:48` — pages**, page_flags(SWAPPED/EXTERNAL/EXTERNAL_MAPPABLE/DECRYPTED/BACKED_UP/PRIV_POPULATED), num_pages, sg, dma_address, swap_storage, backup(file), caching, restore(ttm_pool_tt_restore).
- ttm_pool — `include/drm/ttm/ttm_pool.h:70` — dev, nid, alloc_flags, caching[TTM_NUM_CACHING_TYPES].orders[NR_PAGE_ORDERS].
- amdgpu_bo — `amdgpu/amdgpu_object.h:102` — preferred/allowed_domains, placements[AMDGPU_BO_MAX_PLACEMENTS], placement, tbo(embeds ttm_buffer_object), kmap, flags, vm_bo, parent, xcp_id.
- xe_bo — `xe/xe_bo_types.h:31` — ttm(embeds ttm_buffer_object), backup_obj/parent_obj, flags, vm, tile, placements[XE_BO_MAX_PLACEMENTS], placement, ggtt_node[], vmap, kmap, cpu_caching, devmem_allocation, min_align.
- drm_i915_gem_object — `i915/gem/i915_gem_object_types.h:239` — union{base(drm_gem_object); __do_not_access(ttm_buffer_object)}, ops, vma/lut lists, mm{pages_pin_count, shrink_pin, placements/n_placements, region, res(ttm_resource)}, ttm{backup, created}, flags/mem_flags, pat_index, read/write_domains.
- Embedding: ttm_buffer_object.base *is* a drm_gem_object; amdgpu(tbo)/xe(ttm) embed ttm_bo; i915 unions gem base with ttm_bo (TTM-region path).

#### 2. API families (file:line · role)
- GEM init/handle/lookup: drm_gem_object_init `drm_gem.c:184`(shmem init); drm_gem_handle_create `:552`(→_tail, adds handle+obj ref); drm_gem_handle_delete `:400`(idr_replace→release_handle); drm_gem_object_lookup `:865`(idr); drm_gem_object_release_handle `:366`(close cb + prime-cache remove + vma_node_revoke); drm_gem_object_handle_get `:258`(handle_count++, first grabs obj ref); drm_gem_flink_ioctl `:928`(global name via object_name_idr).
- mmap offset+fault: drm_gem_create_mmap_offset `drm_gem.c:623`; drm_gem_mmap `:1342`(lookup by fake pgoff→); drm_gem_mmap_obj `:1188`(obj ref + vm_ops/funcs->mmap); drm_gem_ttm_mmap `drm_gem_ttm_helper.c:101`(funcs.mmap for TTM, drops gem ref); ttm_bo_vm_fault `ttm_bo_vm.c:321`(reserve→…→unlock) → ttm_bo_vm_fault_reserved `:183`(io_mem_reserve, populate, prefault TTM_BO_VM_NUM_PREFAULT PTEs); i915_gem_mmap_offset_ioctl `i915_gem_mman.c:865`(GTT/WC/WB/UC/FIXED).
- prime export/import: drm_gem_prime_handle_to_fd `drm_prime.c:510`; drm_gem_prime_fd_to_handle `:292`(import cache + handle_create); drm_gem_prime_export `:916`(default, drm_gem_prime_dmabuf_ops); drm_gem_prime_import `:1036`/_import_dev `:968`(self-import shortcut via drm_gem_is_prime_exported_dma_buf → bumps gem ref not f_count); drm_prime_add_buf_handle `:97`(per-file dmabufs/handles rbtrees); drm_prime_pages_to_sg `:850`, drm_prime_sg_to_dma_addr_array `:1082`.
- dma-buf attach/map/cpu: dma_buf_export `dma-buf.c:708`; dma_buf_attach `:1062`(→dynamic_attach); dma_buf_map_attachment `:1169`(pin-if-needed→map_dma_buf→wait KERNEL fence); dma_buf_begin_cpu_access `:1469`; dma_buf_vmap `:1581`(refcounted).
- ttm validate/evict/move/populate/pin: ttm_bo_validate `ttm_bo.c:819`(placement loop: compatible? → alloc_resource → handle_move_mem, -EMULTIHOP bounce); ttm_bo_init_reserved `:930`(vma_offset_add + validate); ttm_bo_evict `:359`(evict_flags→mem_space→handle_move_mem); ttm_bo_handle_move_mem `:120`(create/bind tt, funcs->move); ttm_bo_move_memcpy `ttm_bo_util.c:146`(CPU fallback); ttm_bo_move_accel_cleanup `:700`(pipelined: ghost obj / pipeline-evict + KERNEL fence); ttm_bo_pin/unpin `ttm_bo.c:625`/`:644`; ttm_tt_populate `ttm_tt.c:370`(global-swapout throttle→funcs or ttm_pool_alloc); ttm_pool_alloc `ttm_pool.c:818`; ttm_range_man_alloc `ttm_range_manager.c:60`(drm_mm); ttm_device_init `ttm_device.c:205`; ttm_sys_man_init `ttm_sys_manager.c:35`.
- per-driver create/pin/move: amdgpu — amdgpu_gem_create_ioctl `amdgpu_gem.c:402`(seam)→amdgpu_bo_create `amdgpu_object.c:625`; amdgpu_bo_pin `:925`(scanout pin, forces CPU-visible VRAM); amdgpu_bo_move `amdgpu_ttm.c:498`(VRAM↔GTT blit, TTM_PL_TT multihop); amdgpu_vram_mgr_new `amdgpu_vram_mgr.c:441`(drm_buddy); amdgpu_gem_object_funcs `amdgpu_gem.c:388`; amdgpu_dmabuf_ops `amdgpu_dma_buf.c:355`; amdgpu_dma_buf_move_notify `:467`. xe — xe_bo_create_locked `xe_bo.c:2404`; xe_bo_move `:838`(xe_migrate, XE_PL_TT multihop); xe_gem_object_funcs `:2069`; xe_dmabuf_ops `xe_dma_buf.c:200`; xe_dma_buf_map `:101`. i915 — i915_gem_object_create_region `i915_gem_region.c:107`; i915_ttm_move `i915_gem_ttm_move.c:570`; i915_gem_object_pin_to_display_plane `i915_gem_domain.c:421`(display-pin: set WT/NONE cache, ggtt_pin_ww, mark_scanout).
- dumb (object-side): amdgpu_mode_dumb_create `amdgpu_gem.c:1252`; xe_bo_dumb_create `xe_bo.c:3627`; i915_gem_dumb_create `i915_gem_create.c:167`.

#### 3. Lifecycle & locking (anchors)
- Two GEM refcounts: drm_gem_object.refcount(kref; get/put) vs handle_count (`drm_gem.c:258`, guarded by dev->object_name_lock); first handle grabs an obj ref, last handle-release clears flink name and breaks the gem↔dma_buf ref loop.
- TTM own kref (ttm_buffer_object.kref, distinct from base gem ref): ttm_bo_release `ttm_bo.c:250` on last put individualizes resv (ttm_bo_individualize_resv), and if not idle resurrects via kref_init + queues delayed_delete on bdev->wq; ttm_bo_delayed_delete `:236` waits BOOKKEEP fences (MAX_SCHEDULE_TIMEOUT) then cleanup_memtype_use.
- dma_resv is THE BO lock: bo->base.resv (==&_resv, or dma_buf->resv for imports); dma_resv_assert_held guards validate/move/pin/map_attachment; last-resort 30*HZ wait in ttm_bo_release if resv alloc fails.
- LRU locks: ttm_device.lru_lock(spinlock) protects per-manager lru[priority], unevictable, ddestroy; pin/unpin swap between LRU tail and bulk_move; ttm_lru_bulk_move requires all BOs share one resv.
- Pool locks: ttm_pool.c global shrinker_lock + pool_shrink_rwsem over shrinker_list; ttm_pool_shrink `ttm_pool.c:381` frees one page/order round-robin.
- Move fences (pipelined): ttm_resource_manager.eviction_fences[TTM_NUM_MOVE_FENCES] + eviction_lock; ttm_bo_move_accel_cleanup adds DMA_RESV_USAGE_KERNEL fence, builds ghost object for non-evict moves; TTM fault waits the pipelined-move fence (ttm_bo_vm_fault_idle).
- Prime cache: drm_prime_file_private{dmabufs, handles rbtrees} (`drm_prime.h:45`), guarded by file_priv->prime.lock.

#### 4. Hard-coded limits (value · file:line)
- Placement arrays: AMDGPU_BO_MAX_PLACEMENTS=3 `amdgpu_object.h:40`; XE_BO_MAX_PLACEMENTS=3 `xe_bo_types.h:23`.
- TTM_NUM_MEM_TYPES=9 `ttm_resource.h:38`; TTM_MAX_BO_PRIORITY=4U `:37`; TTM_NUM_MOVE_FENCES=8 `:61`; TTM_NUM_CACHING_TYPES=3 `ttm_caching.h:30`.
- Pool orders: NR_PAGE_ORDERS = MAX_PAGE_ORDER+1 `mmzone.h:38` (per caching type); TTM_ALLOCATION_POOL_BENEFICIAL_ORDER max = (n)&0xff `ttm_allocation.h:7`.
- Mem types TTM_PL_SYSTEM=0/TT=1/VRAM=2/PRIV=3 `ttm_placement.h:51-54`.
- Mmap fake-offset space (64-bit): DRM_FILE_PAGE_OFFSET_SIZE=(0xFFFFFFFFUL>>PAGE_SHIFT)*256, START=(…>>PAGE_SHIFT)+1 `drm_vma_manager.h:37-38`.
- Delayed-delete workqueue max_active=16 `ttm_device.c:205`; ttm_bo_release last-resort wait 30*HZ `ttm_bo.c`.
- amdgpu VRAM default block 2MB / HPAGE_PMD_NR `amdgpu_vram_mgr.c:441`.

#### 5. Version-specific facts @ v7.0
- dmem cgroup integrated into TTM: ttm_resource.css(dmem_cgroup_pool_state, `ttm_resource.h:263`) + ttm_resource_manager.cg(dmem_cgroup_region, `:199`); managers charge/uncharge memory per region.
- ttm_backup present: ttm_tt.backup + restore fields (`ttm_tt.h:48`), TTM_TT_FLAG_BACKED_UP/PRIV_POPULATED bits, ttm_tt_backup `ttm_tt.c:281`→ttm_pool_backup; dedicated `drivers/gpu/drm/ttm/ttm_backup.c`; xe wires it via `xe_shrinker.c`.
- New header `include/drm/ttm/ttm_allocation.h`: TTM_ALLOCATION_* flags (POOL_USE_DMA_ALLOC/USE_DMA32, PROPAGATE_ENOSPC); ttm_device_init/ttm_pool_init now take a single `alloc_flags` (replacing old use_dma_alloc/use_dma32 bools); ttm_bo_validate honors PROPAGATE_ENOSPC.
- Modern LRU/bulk-move era: ttm_lru_item + ttm_lru_bulk_move.cursor_list traversal (`ttm_resource.h:316`); bulk move requires shared resv.
- No AGP in this area (TTM has no AGP manager; TT backing is ttm_range/ttm_tt only).
- gpuva list embedded in drm_gem_object (GPUVM, DRM_GPUVM_IMMEDIATE_MODE).
- TTM core has NO tracepoints (grep of drivers/gpu/drm/ttm finds none).

#### 6. Suggested page topics (anchor-symbol justification; thin→merge flags)
- gem-object — drm_gem_object + funcs, init, refcount. Strong.
- gem-handles(+flink) — handle_create/delete/lookup, flink/open names, handle-vs-obj refs. Strong.
- gem-mmap(+vma-manager+ttm fault) — drm_gem_mmap_obj/mmap, drm_vma_offset_node, ttm_bo_vm_fault(_reserved). Strong. Fold gem-ttm-helper (thin: mmap/vmap/dumb_map shims) in here.
- prime/dma-buf sharing (render↔display) — handle↔fd, self-import, import/export cache, dma_buf_ops, attach/map/cpu-access, driver dmabuf_ops + move_notify. Strong; carry the display-pin note here.
- ttm-bo — ttm_buffer_object, init_reserved, validate, pin, delayed destroy/resurrect. Strong. Fold ttm-device as a subsection, or keep slim standalone — it is the driver contract.
- ttm-resource/placement — ttm_resource/manager/place/placement, mem types, LRU + bulk-move, range/sys managers. Strong. Merge ttm-eviction/LRU here (ttm_bo_evict + eviction_valuable/evict_flags) — too thin to stand alone.
- ttm-tt — page array, populate/unpopulate, swap/backup. Strong (backup is a v7.0 headline).
- ttm-pool — cached/WC pools, orders, shrinker. Strong.
- ttm-moves — memcpy + ghost/pipelined cleanup + per-driver move incl. multihop. Strong.
- per-driver BO pages — amdgpu_bo (vram/gtt mgr), xe_bo (xe_ttm_*_mgr), i915 object (+i915_gem_ttm.c, intel_memory_region.c). Strong; fold dumb-create (3 thin shims) and the display-pin story into these or into prime.
- Flag: dumb-buffers and gem-ttm-helper are too thin as own pages → merge as above. intel_memory_region / amdgpu_gtt_mgr / xe_ttm_stolen_mgr are minor → fold into ttm-resource or per-driver pages. dma_resv is load-bearing but out-of-area (locking primitive) → reference only.

#### 7. Tracepoints (file:line)
- amdgpu `amdgpu_trace.h`: TRACE_EVENT(amdgpu_bo_create) `:116` (fired in amdgpu_bo_create), TRACE_EVENT(amdgpu_bo_move) `:524` (+ amdgpu_ttm_bo_move et al.).
- xe `xe_trace_bo.h`: DECLARE_EVENT_CLASS(xe_bo) `:23` → xe_bo_cpu_fault `:46`, xe_bo_validate `:51`, xe_bo_create `:56`; TRACE_EVENT(xe_bo_move) `:61` (fired in xe_bo_move).
- i915 `i915_trace.h`: i915_gem_object_create `:21`, i915_gem_object_pwrite `:106`, i915_gem_object_pread `:126`, i915_gem_object_fault `:146`.
- dma-buf `drivers/dma-buf/dma-buf.c`: has its own events (trace_dma_buf_export in dma_buf_export `:708`).
- TTM core: none — no TRACE_EVENT/trace_ anywhere under `drivers/gpu/drm/ttm/`.
### Area F: GPU VM, allocators & execution — COMPLETE (recorded 2026-07-12)

(Paths under `drivers/gpu/drm/` unless `include/`. amdgpu = `amd/amdgpu/`, dm = `amd/display/amdgpu_dm/`.)

#### 1. Core structs (definition file:line, role)
- drm_gpuva `include/drm/drm_gpuvm.h:74` — one VA mapping (va.addr/range, gem.obj/offset, vm_bo backref, rb node, flags); flags enum `:45` (INVALIDATED/SPARSE).
- drm_gpuvm `include/drm/drm_gpuvm.h:229` — per-VM VA manager: mm_start/mm_range, rb.tree+list, kref, kernel_alloc_node, ops, r_obj (resv GEM), extobj{list,lock} `:296`, evict{list,lock} `:318`, bo_defer llist `:340`; flags enum `:194` (RESV_PROTECTED, IMMEDIATE_MODE).
- drm_gpuvm_bo `include/drm/drm_gpuvm.h:666` — (vm,obj) tuple, kref, evicted bool, list.gpuva + entry.{gem,extobj,evict}.
- drm_gpuva_op / ops / map_req `:977 / :1017 / :1095`; op_type enum `:826`; op_map/unmap/remap/prefetch `:859/898/940/963`; drm_gpuvm_ops `:1139` (sm_step_map/unmap/remap callbacks); drm_gpuvm_exec `:533`.
- drm_mm_node `include/drm/drm_mm.h:157` — allocated range (color/start/size + interval/hole rb); drm_mm `:190` (hole_stack, interval_tree, holes_size/addr); drm_mm_scan `:227` (eviction roster, stack-alloc); insert_mode enum `:70` (BEST/LOW/HIGH/EVICT/ONCE/HIGHEST/LOWEST).
- drm_buddy_block `include/drm/drm_buddy.h:24` — header bitfield (OFFSET/STATE/CLEAR/ORDER), left/right/parent, rb|link union; drm_buddy `:65` — free_trees (rb) + roots, n_roots, max_order, chunk_size, size/avail/clear_avail; flags `:17-22`.
- drm_suballoc_manager `include/drm/drm_suballoc.h:24` (hole, olist, flist[MAX_QUEUES], size/align); drm_suballoc `:42` (soffset/eoffset, fence).
- drm_exec `include/drm/drm_exec.h:17` — flags, ww ticket, objects[], num/max_objects, contended, prelocked; flags `:9` INTERRUPTIBLE_WAIT, `:10` IGNORE_DUPLICATES.
- drm_sched_entity `include/drm/gpu_scheduler.h:82`; drm_sched_rq `:251`; drm_sched_fence `:264` (scheduled + finished dma_fences, parent=hw fence, deadline); drm_sched_job `:340` (s_fence, entity, sched, credits, karma, dependencies xarray, list); drm_sched_backend_ops `:412` (prepare/run/timedout/free_job); drm_gpu_scheduler `:573` (ops, credit_limit/credit_count, num_rqs, sched_rq[], pending_list, work_run_job/free_job/tdr); priority enum `:65`.
- amdgpu_vm_bo_base `amdgpu/amdgpu_vm.h:200` (vm,bo,next,vm_status,moved); amdgpu_vm `:337` (rb `va`, eviction_lock+evicting `:344`, status_lock `:349`, lists evicted/relocated/moved/idle/evicted_user/invalidated/done/freed `:362-394`, root, immediate+delayed sched entities `:401`, tlb_seq, reserved_vmid[]); level enum `:191` (PDB3..PTB); amdgpu_vm_manager `:454`.
- amdgpu_bo_va_mapping `amdgpu/amdgpu_object.h:64` (rb interval, start/last/offset/flags); amdgpu_bo_va `:76` (base, ref_count, valids/invalids lists, queue_refcount+userq_va_mapped `:98`).
- xe_vma `xe/xe_vm_types.h:99` (embeds `drm_gpuva` `:101`, tile_present/invalidated masks, ufence, attr); xe_userptr_vma `:171`; xe_vm `:178` (embeds `drm_gpuvm` `:180` + `drm_gpusvm` svm `:185`, pt_root[], vm->lock rw_semaphore `:241`, snap_mutex, rebind_list, userptr, preempt{exec_queues,rebind_work} `:274`, usm.asid); flags `:226` (LR_MODE/FAULT_MODE/SCRATCH).
- i915_address_space `i915/gt/intel_gtt.h:247` (embeds `drm_mm` `:251`, `mutex` `:266`, kref+resv_ref, is_ggtt/is_dpt, VM_CLASS_GGTT/PPGTT/DPT `:270-272`, pte_encode/insert_entries vfuncs); i915_vma `i915/i915_vma_types.h:135` (embeds `drm_mm_node` `:136`, flags atomic, PIN_MASK 0x3ff, GLOBAL/LOCAL_BIND, GGTT, SCANOUT bit :215, i915_active).
- i915_dpt `i915/display/intel_dpt.c:20` (embeds i915_address_space vm, dpt_obj).

#### 2. API families (file:line, role)
- gpuvm: init `drm_gpuvm.c:1093`; bo_create `:1575`, bo_obtain `:1826`, bo_obtain_prealloc `:1902`, bo_put `:1678`, bo_evict `:1958`; gpuva_link `:2094`/map `:2296`/remap `:2316`/unmap `:2345`; sm_map `:2670`, sm_unmap `:2712`, sm_map_ops_create `:2999`, sm_unmap_ops_create `:3073`; prepare_objects `:1288`, prepare_range `:1315`, validate `:1522`, resv_add_fence `:1546`.
- drm_mm: reserve_node `drm_mm.c:451`, insert_node_in_range `:515`, remove_node `:628`, scan_init_with_range `:702`, scan_add_block `:746`, scan_remove_block `:837`, scan_color_evict `:878`, init `:929`.
- drm_buddy: init `drm_buddy.c:299`, alloc_blocks `:1099`, free_block `:529`, free_list `:579`, block_trim `:991`.
- drm_suballoc: manager_init `drm_suballoc.c:63`, manager_fini `:95`, new `:315`, free `:400`.
- drm_exec lock loop: init `drm_exec.c:81`, cleanup(retry) `:123`, lock_obj `:209`, prepare_obj `:291`, prepare_array `:323`, fini `:104` (`drm_exec_until_all_locked` macro in header wraps cleanup).
- scheduler: job_init `sched_main.c:800`, job_arm `:858`, job_add_dependency `:884`, job_add_resv_dependencies `:960`, sched_init `:1317`, run_job_work `:1231`; entity_init `sched_entity.c:58`, push_job `:576`, pop_job `:464`, flush `:283`, destroy `:356`; fence scheduled `sched_fence.c:65`, finished `:80`, alloc `:208`, init `:225`.
- amdgpu vm: init `amdgpu_vm.c:2580`, validate `:592`, bo_add `:1735`, bo_map `:1845`, bo_unmap `:1956`, bo_update `:1262`, update_range `:1108`, clear_freed `:1548`, handle_moved `:1610`; GEM_VA uapi `amdgpu_gem.c:820` (amdgpu_gem_va_ioctl); VMID grab `amdgpu_ids.c:384`, alloc_reserved `:472`, reset_all `:553`; GART bind `amdgpu_gart.c:463`/unbind `:301`/map `:347`.
- xe vm: create `xe_vm.c:1477`, close_and_put `:1732`, create_ioctl `:1924`, bind_ioctl `:3611`, rebind `:687`, vma_create `:990`, vma_destroy `:1118`, lock `:3931`; PT: pt_create `xe_pt.c:103`, update_ops_prepare `:2282`, run `:2518`, fini `:2696`, abort `:2722`; GGTT: init `xe_ggtt.c:478`, node_insert `:671`, insert_bo `:939`, map_bo `:762`.
- i915 vma: bind `i915_vma.c:474`, pin `:1624`, pin_ww `:1434`, ggtt_pin `:1690`, unbind `:2191`.
- display pin: amdgpu amdgpu_bo_pin `amdgpu_object.c:925` ← prepare_fb `dm/amdgpu_dm_plane.c:925` (domain=AMDGPU_GEM_DOMAIN_VRAM `:965`, pin `:968`); i915 intel_plane_pin_fb `intel_fb_pin.c:263` → pin_to_ggtt `:112` / pin_to_dpt `:26`; DPT create `intel_dpt.c:246`, pin_to_ggtt `:126`; xe xe_pin_fb_vma → __xe_pin_fb_vma_dpt `xe_fb_pin.c:82` / __xe_pin_fb_vma_ggtt `:220` (select `:329/331`).

#### 3. Lifecycle & locking (anchors)
- gpuvm refcount: drm_gpuvm.kref `drm_gpuvm.h:273`, drm_gpuvm_bo.kref `:688`. Lock protocol: `DRM_GPUVM_RESV_PROTECTED` `:199` → gpuva lists under the GEM/VM dma_resv; else default/`IMMEDIATE_MODE` `:209` uses per-gpuva `gpuva.lock`; `drm_gpuvm_resv_held()` macro `:420`. extobj/evict lists have own spinlocks `:312/:334`; bo_defer llist for deferred vm_bo free `:340`.
- amdgpu: status_lock (spinlock `amdgpu_vm.h:349`) protects all vm_bo state lists; eviction_lock (mutex `:344`) + `evicting` bool serialize PT updates vs TTM eviction; per-bo_va `ref_count` under BO resv `object.h:80`; user-queue keep-alive `queue_refcount`/`userq_va_mapped` `:98`. State machine: evicted→relocated(PD/PT)|moved(perVM)→idle; evicted_user|invalidated→done `:355-388`.
- xe: `vm->lock` rw_semaphore outermost `xe_vm_types.h:241`; VM resv for BO residency; snap_mutex for devcoredump `:246`; userptr via drm_gpusvm notifier_lock (mmu_notifier, doc `:124`); LR/FAULT_MODE use preempt-fences, legacy uses dma-fences; VM kref/destroy via drm_gpuvm + destroy_work `:260`.
- i915: `vm->mutex` protects vma + bound/unbound lists `intel_gtt.h:266`; two krefs: `ref` (vm lifetime) `:248` + `resv_ref` (resv lock) `:268`; vma pin encoded in flags PIN_MASK 0x3ff, `vm_ddestroy` defers vm free until vma gone `i915_vma_types.h:229`.
- scheduler: job owns s_fence (scheduled+finished) created at job_init/arm; `parent` = hw fence from run_job signals `finished` `gpu_scheduler.h:289-294`; finish_cb/work union `:373`; dependencies xarray drained by last_dependency; entity queues via spsc.

#### 4. Hard-coded limits (value, file:line)
- DRM_BUDDY_MAX_ORDER = 63−12 = 51, order-0 ≥ SZ_4K `drm_buddy.h:57`.
- AMDGPU_NUM_VMID = 16 `amdgpu_ids.h:34`; AMDGPU_MAX_VMHUBS = 13 `amdgpu_vm.h:156`; AMDGPU_VM_MAX_UPDATE_SIZE = 0x3FFFF `:52`; PT levels PDB3..PTB = 5 `:191`; max_pfn = `vm_size << 18` `amdgpu_vm.c:2405`; fault-stop modes 0/1/2 `amdgpu_vm.h:145`.
- DRM_SCHED_PRIORITY_COUNT = 4 (KERNEL/HIGH/NORMAL/LOW) `gpu_scheduler.h:71`; num_rqs ≤ COUNT; `credit_limit` is u32, driver-set (no hard constant) `:575`.
- XE_VM_MAX_LEVEL = 4 `xe/xe_pt_types.h:27`.
- GEN8_3LVL_PDPES = 4 → 4-level/48-bit PPGTT `i915/gt/intel_gtt.h:133`; 32-bit platforms capped to 2 GB GGTT `i915/gt/intel_ggtt.c:1161`.
- suballoc queues: `flist[DRM_SUBALLOC_MAX_QUEUES]` `drm_suballoc.h:28`.

#### 5. Version-specific facts @ v7.0
- drm_gpuvm adoption: xe yes (`Kconfig:43 select DRM_GPUVM`, xe_vm embeds drm_gpuvm); amdgpu NO — keeps its own rb-tree `amdgpu_vm` (Kconfig selects only DRM_SCHED). i915 uses its own drm_mm-based address_space (no gpuvm).
- SVM: `drm_gpusvm.c` (init `:383`, range_get_pages `:1596`) and `drm_pagemap.c` both present; only xe uses them (`Kconfig:42 select DRM_GPUSVM`, xe_svm.c, xe_vm.svm.gpusvm). amdgpu does not use drm_gpusvm.
- amdgpu user queues + fences present: `amdgpu_userq.c`, `amdgpu_userq_fence.c`, `amdgpu_eviction_fence.c` exist; reflected by amdgpu_vm.evicted_user list `:382` and amdgpu_bo_va.queue_refcount/userq_va_mapped `:98`.
- drm_buddy reworked to rb-tree free lists at v7.0: `free_trees`/`roots` `drm_buddy.h:66-76` (older kernels used `free_list`); `drm_buddy_reset_clear` `:159` new.
- gpuvm deferred cleanup new: `drm_gpuva_unlink_defer()` `drm_gpuvm.h:156` + `bo_defer` llist `:340`.
- Scheduler trace header MOVED: not `include/trace/events/gpu_scheduler.h` (absent) → now `scheduler/gpu_scheduler_trace.h`; scheduler uses credits + multi-rq model (`credit_limit`/`num_rqs`).

#### 6. Suggested page topics (justification / merge flags)
- gpuvm-overview — strong: drm_gpuvm/gpuva/gpuvm_bo + sm_map/sm_unmap state machine, lock protocol. KEEP.
- drm-mm — strong: range allocator + eviction scan roster. KEEP.
- drm-buddy — strong: rb free-tree rework, flags. KEEP.
- drm-suballoc — THIN (2 structs, ~4 fns); merge into drm-buddy or an "allocators" page.
- drm-exec — medium: lock loop + retry idiom, INTERRUPTIBLE_WAIT. KEEP (short).
- gpu-scheduler — strong: job/fence lifecycle, credits, priorities, tracepoints. KEEP.
- amdgpu-vm — strong; fold amdgpu PT update backends (amdgpu_vm_pt.c / amdgpu_vm_sdma.c vs amdgpu_vm_cpu.c, update_funcs `amdgpu_vm.h:310`) as a section, not a separate page.
- xe-vm — strong: drm_gpuvm+VM_BIND+preempt vs dma-fence, xe_pt. KEEP.
- i915-ppgtt/ggtt — medium: i915_address_space + i915_vma pin; single page (add DPT). KEEP.
- scanout-pin story — KEEP (cross-driver): i915/xe scanout in GGTT/DPT vmas (SCANOUT bit, intel_fb_pin/intel_dpt/xe_fb_pin) vs amdgpu pinned VRAM (amdgpu_bo_pin, DOMAIN_VRAM) — explains why not paged through per-process VM.
- userptr — medium; could be a section under xe-vm + amdgpu-vm rather than standalone (xe now routes userptr through drm_gpusvm notifier_lock).
- SVM — xe-only; KEEP as its own short page (drm_gpusvm + drm_pagemap), note amdgpu non-use.
- MISSING/consider: a short VMID/GART note (amdgpu_ids.c/amdgpu_gart.c) — either its own stub or a section in amdgpu-vm.

#### 7. Tracepoints (file:line)
- scheduler `scheduler/gpu_scheduler_trace.h`: class `drm_sched_job` `:57` → `drm_sched_job_queue` `:86`, `drm_sched_job_run` `:91`; `drm_sched_job_done` `:96`; `drm_sched_job_add_dep` `:112`; `drm_sched_job_unschedulable` `:133`.
- amdgpu `amdgpu/amdgpu_trace.h`: `amdgpu_vm_grab_id` `:214`, `amdgpu_vm_bo_map` `:241`, `amdgpu_vm_bo_unmap` `:265`, `amdgpu_vm_update_ptes` `:322`, `amdgpu_vm_set_ptes` `:365`, `amdgpu_vm_copy_ptes` `:391`, `amdgpu_vm_flush` `:412`; also `amdgpu_sched_run_job` `:190`.
- xe `xe/xe_trace_bo.h`: class `xe_vma` `:88` → bind `:133`, pf_bind `:138`, unbind `:143`, userptr_rebind_worker/exec `:148/153`, rebind_worker/exec `:158/163`, userptr_invalidate `:168`, invalidate `:173`, evict `:178`; class `xe_vm` `:188` → create `:216`, cpu_bind `:226`, rebind_worker_enter/retry/exit `:236/241/246`, ops_fail `:251`. Exec queues in `xe/xe_trace.h` (class `:69`).
- i915 `i915/i915_trace.h`: `i915_vma_bind` `:58`, `i915_vma_unbind` `:84`.
- NONE: drm_mm.c, drm_buddy.c, drm_exec.c, drm_gpuvm.c, drm_suballoc.c define no tracepoints (verified).

## Directory organization

All pages under `docs/drm/`, ten groups (plus one formats subdirectory, following the `docs/dp/` precedent for a third level):

```
docs/drm/
├── core/     the drm_device/driver/registration foundation (1)
├── pixel/    pixel formats & color management (9 + formats/ 7)
│   └── formats/   family-grouped fourcc pages
├── kms/      the KMS objects and their cooperation narratives (18)
├── atomic/   atomic state/locking/commit infrastructure (3)
├── ioctl/    the uapi surface: dispatch, files, auth, KMS entry points (9)
├── timing/   display timing, vblank, VRR/PSR, fences, syncobj (7)
├── gem/      GEM object/handle/mmap/prime (4)
├── ttm/      TTM machinery + per-driver buffer objects (9)
├── gpuvm/    GPU virtual memory + allocators (8)
└── sched/    GPU scheduler + drm_exec (2)
```

Rationale: the prompt's seven H3 areas map onto pixel/, kms/, ioctl/, timing/, ttm/, gem/, gpuvm/; atomic/ is split out of ioctl/ because the state/commit machinery is driver-facing infrastructure, not uapi (and the primary draft corpus reached the same split); sched/ holds the two execution helpers the memory pages depend on; core/ holds the one foundation page every other page presumes. kms/ keeps the two prompt-required cooperation narratives (modeset-pipeline, steady-state) beside the objects they narrate.

## Page catalog

Tags: [prompt] = explicitly in a prompt.md bullet (or a granularity split of one, marked "split"); [curated] = gap-fill the prompt's "curate new pages where you see fit" mandates.

### core/

| page | scope (anchor symbols) | tag |
|---|---|---|
| drm-device.md | struct drm_device / drm_driver, minor/render nodes, drm_dev_alloc/init/register/unregister, drmm managed-resource machinery (drmm_add_action, drmm_kmalloc), driver feature flags (DRIVER_MODESET/GEM/ATOMIC), debugfs/sysfs registration points; amdgpu_drv.c + i915_driver.c/xe_device.c driver-struct instances | [curated] |

### pixel/

| page | scope (anchor symbols) | tag |
|---|---|---|
| color-formats.md | index/overview: fourcc_code(), struct drm_format_info `drm_fourcc.h:61`, __drm_format_info table `drm_fourcc.c:175` (~130 entries), drm_get_format_info + driver get_format_info override, format accessor inlines, IN_FORMATS blob + modifier advertising (create_in_formats, __drm_universal_plane_init), 64-format WARN cap; landing page for formats/ | [curated] |
| formats/rgb-8888.md | XRGB8888, XBGR8888, ARGB8888, ABGR8888, RGBA8888: byte/channel layouts (7h figures), format-info rows, amdgpu rgb_formats/overlay_formats/cursor_formats + i915 arrays advertising, alpha semantics | [prompt] |
| formats/rgb-2101010.md | XRGB2101010, XBGR2101010, ARGB2101010, ABGR2101010: 10bpc packing, format-info rows, driver arrays (amdgpu rgb_formats, skl/icl arrays) | [prompt] |
| formats/rgb-16161616.md | XRGB/XBGR/ARGB/ABGR16161616 integer (amdgpu) + XRGB/XBGR/ARGB/ABGR16161616F FP16 HDR (i915 icl_hdr + amdgpu alpha list), 64bpp layouts | [prompt] |
| formats/rgb565-and-legacy.md | RGB565, XRGB1555 (i8xx_primary_formats), C8 indexed (is_color_indexed; i915-only): 16/8bpp layouts, legacy drm_mode_legacy_fb_format mapping | [prompt] |
| formats/yuv-420-semiplanar.md | NV12, NV21, P010, P012, P016: two-plane layouts, hsub/vsub=2, chroma siting, driver arrays (amdgpu video/overlay_formats, glk/icl planar) | [prompt] |
| formats/yuv-422-packed.md | YUYV, YVYU, UYVY, VYUY (8-bit) + Y210, Y212, Y216: packed 4:2:2 layouts, icl Y-plane arrays | [prompt] |
| formats/yuv-444-packed.md | XYUV8888, XVYU2101010, XVYU16161616, XVYU12_16161616: packed 4:4:4 layouts, icl_hdr array | [prompt] |
| bpc-and-bpp.md | bits-per-component vs bits-per-pixel: drm_format_info cpp/char_per_block/bpp helpers, drm_display_info.bpc consumption (the field tour is kms/edid.md's), max_bpc/max_requested_bpc property pair + attach helper, HDMI 8/10/12 clamp, seam-level intel_dp_max_bpp/min_bpp link feed; amdgpu DC bpc handling | [prompt] |
| pitch-and-layout.md | framebuffer memory layout: drm_format_info_min_pitch, block_w/h/char_per_block math, drm_framebuffer pitches[4]/offsets[4]/modifier, multi-plane offsets (NV12 worked example), framebuffer_check validation | [curated] |
| color-gamut.md | colorspace/encoding/range: enum drm_colorspace + Colorspace property (hdmi/dp variants), enum drm_color_encoding/drm_color_range + per-plane props, Broadcast RGB, HDR_OUTPUT_METADATA blob + hdr_metadata_infoframe/hdr_output_metadata structs, drm_display_info color_formats/hdr_sink_metadata consumption (field tour is kms/edid.md's) | [prompt] |
| color-curve.md | transfer functions: enum drm_colorop_curve_1d_type (sRGB/PQ_125/BT2020/Gamma22 + inverses), EOTF/OETF semantics, amdgpu color_gamma.c curve math (translate_from_linear_space, build_pq, MAX_HW_POINTS regions), i915 curve handling | [prompt] |
| gamma-degamma.md | LUT machinery: struct drm_color_lut/drm_color_lut32, drm_color_lut_check/lut32_check tests, lut_extract/size helpers, legacy gamma_set ioctls + gamma_store, new load/fill gamma-palette helper family, driver LUT sizes (amdgpu 4096/256, i915 per-platform table) and LUT→HW extraction, citing intel_color_funcs.load_luts as the consumer (the hook order is color-pipeline.md's) | [prompt] |
| ctm.md | color transform matrices: struct drm_color_ctm (S31.32 sign-magnitude) + drm_color_ctm_3x4, drm_color_ctm_s31_32_to_qm_n, CTM property/state blob, amdgpu CTM→DC, i915 intel_csc_matrix/ILK_CSC_COEFF_* | [prompt] |
| color-pipeline.md | the per-CRTC DEGAMMA_LUT→CTM→GAMMA_LUT pipeline: drm_crtc_enable_color_mgmt, *_SIZE props, crtc_state blobs + color_mgmt_changed, amdgpu_dm_color update path; owns struct intel_color_funcs and the commit-time hook order (check/commit_noarm/arm/load_luts; LUT data extraction is gamma-degamma.md's) | [curated] |
| colorop-pipeline.md | NEW v7.0 per-plane color pipeline: struct drm_colorop/drm_colorop_state, enum drm_colorop_type (1D_CURVE/1D_LUT/CTM_3X4/MULTIPLIER/3D_LUT), COLOR_PIPELINE plane property, DRM_CLIENT_CAP_PLANE_COLOR_PIPELINE, per-type init helpers, atomic COLOROP routing; amdgpu_dm_colorop.c (LUT3D_SIZE 17), intel_colorop.c/intel_color_pipeline.c | [curated] |

### kms/

| page | scope (anchor symbols) | tag |
|---|---|---|
| mode-config.md | struct drm_mode_config: the seven locks, object lists/counts/idrs, min/max dims, funcs/helper_private, standard-property pointer registry, drmm_mode_config_init/reset/cleanup, drm_modeset_register_all/unregister_all | [curated] |
| object-model.md | struct drm_mode_object: id/type/kref/free_cb, object_idr add/register/unregister/find/get/put, DRM_OBJECT_MAX_PROPERTY=64, the three lifetime models (drmm-managed vs manual cleanup vs refcount+free_cb) | [curated] |
| property.md | struct drm_property (+flags RANGE/ENUM/BITMASK/OBJECT/BLOB, ATOMIC/IMMUTABLE), drm_property_create family, enum lists, struct drm_property_blob lifecycle (create/get/put, blob_lock, per-file blobs), drm_object_attach_property/set/get_value, standard-property creation (drm_connector_create_standard_properties) | [curated] |
| framebuffer.md | struct drm_framebuffer + funcs: base refcount/free_cb, format/pitches/offsets/modifier/obj[], init/cleanup/remove semantics, fb_list+fb_lock, filp_head per-file ownership, driver wrappers amdgpu_framebuffer / intel_framebuffer; creation entry (fb_create) at seam to ioctl/addfb2 | [prompt] |
| plane.md | struct drm_plane/drm_plane_state + funcs + helper_funcs: plane types PRIMARY/CURSOR/OVERLAY, universal planes, format_types/modifiers arrays, src 16.16 vs crtc rects, fence field, possible_crtcs (32-plane cap), drm_universal_plane_init; wrappers dm_plane_state/amdgpu_dm_plane_init + intel_plane/intel_plane_state | [prompt] |
| plane-composition.md | composition properties: alpha/rotation/zpos(+normalized)/pixel_blend_mode (drm_blend.c helpers), scaling_filter, FB_DAMAGE_CLIPS + damage helpers, hotspot/cursor offsets; amdgpu + i915 per-plane blending wiring | [curated] |
| crtc.md | struct drm_crtc/drm_crtc_state + funcs + helper_funcs: init_with_planes/drmm variant/cleanup, 32-CRTC cap, primary/cursor links, gamma_size/store, mode/adjusted_mode/blob, masks, event field, sharpness prop (new); wrappers amdgpu_crtc/dm_crtc_state(dc_stream_state) + intel_crtc/intel_crtc_state | [prompt] |
| encoder.md | struct drm_encoder + funcs + helper_funcs: encoder_type TMDS for DP/eDP, possible_crtcs/possible_clones (32-encoder cap), init/drmm/cleanup, bridge_chain field; amdgpu_encoder/amdgpu_dm_encoder_init + intel_encoder/intel_ddi_init seam (DP protocol out) | [prompt] |
| connector.md | struct drm_connector/drm_connector_state + funcs + helper_funcs: registration_state machine + dynamic (MST) registration, display_info as a field (its tour is kms/edid.md's), status/force/epoch_counter, eld+eld_mutex, tile, panel-orientation, Content Protection property (transport out of scope), connector_list iteration rules; wrappers amdgpu_dm_connector + intel_connector | [prompt] |
| bridge.md | struct drm_bridge + drm_bridge_funcs + chain model: NEW v7.0 refcounting (drm_private_obj base + kref, drm_bridge_get/put), add/remove/attach, bridge_chain on encoder; the evidence-backed x86 reality (amdgpu/i915/xe display do not use drm_bridge; DSI excluded) and what uses it instead | [prompt] |
| edid.md | EDID parsing to display_info: opaque struct drm_edid API (drm_edid_read/connector_update/add_modes/free) superseding raw struct edid, block validation (EDID_LENGTH 128, extensions), OWNS the struct drm_display_info field tour (bpc/color_formats/hdmi fields/quirks/monitor_range — connector/bpc-and-bpp/color-gamut cite it), edid_blob_ptr property; DP EDID transport is dp/'s | [curated] |
| hotplug-detect.md | runtime detection: connector status enum + polling (output_poll_execute, 10s period), drm_helper_probe_single_connector_modes, detect_ctx contract, drm_kms_helper_hotplug_event/connector_hotplug_event, drm_helper_hpd_irq_event vs drm_connector_helper_hpd_irq_event, link-status property, epoch_counter; driver HPD glue at seam (DPCD/AUX out) | [curated] |
| probe-init.md | how the objects come to exist in the driver: creation order + registration split (create pre-register, expose via drm_dev_register→drm_modeset_register_all); amdgpu_dm chain (dm_early_init→amdgpu_dm_init→mode_config_init→initialize_drm_device: planes→crtcs→connectors→encoders) vs intel_display_driver probe staging (early_probe→noirq→nogem→probe→register), xe glue | [prompt] |
| modeset-pipeline.md | the cross-object modeset narrative: which callbacks fire on which objects in what order for a full DP/eDP modeset — atomic check across the object graph (mode fixup, encoder/bridge/crtc checks), disable sequence, enable sequence (crtc enable→encoder pre_enable/enable at link-training seam), helper-callback contract map (drm_modeset_helper_vtables.h); amdgpu DC stream/pipe mapping + intel modeset sequence | [prompt] |
| steady-state.md | frame delivery after modeset: page-flip/plane-update repetition, fence-gated flips (prepare_fb→wait_for_fences), commit event delivery, async flip path, cursor updates, frontbuffer tracking (intel) / surface flips (amdgpu dc); owns the intel pipe-update tracepoint set (trace_intel_pipe_update_start/vblank_evaded/end intel_crtc.c:594/604/696, trace_intel_crtc_flip_done, trace_intel_plane_async_flip) + the amdgpu flip ISR chain (prepare_flip_isr→dm_pflip_high_irq) | [prompt] |
| writeback.md | writeback connectors: drm_writeback_connector, WRITEBACK_FB_ID/PIXEL_FORMATS/OUT_FENCE_PTR props, job queue/cleanup; amdgpu_dm_wb.c is the only in-scope implementor (i915/xe expose none — evidence) | [curated, optional] |
| privacy-screen.md | eDP privacy screens on x86/ACPI: drm_privacy_screen object/notifier/lookup, sw/hw_state props, drm_privacy_screen_x86.c providers (ThinkPad HKEY.GSSS, Chrome GOOG0010), connector attach + i915 use | [curated, optional] |
| panic.md | drm_panic: the panic scanout path, drm_panic_register/unregister, get_scanout_buffer plane hook implemented by all three stacks (amdgpu_dm_plane, intel_plane, xe_panic), drawing into the live framebuffer | [curated, optional] |

### atomic/

| page | scope (anchor symbols) | tag |
|---|---|---|
| atomic-state.md | struct drm_atomic_state + `__drm_*_state` arrays (crtcs/planes/connectors/colorops/private_objs), get_*_state/add_affected_* families, alloc/clear/put lifetime, checked/duplicated bits, default state helpers (reset/duplicate/destroy from drm_atomic_state_helper.c), drm_private_obj/drm_private_state | [prompt, split of "KMS atomic"] |
| modeset-locking.md | drm_modeset_lock/drm_modeset_acquire_ctx: ww-mutex EDEADLK backoff protocol (contended/backoff/retry loop), DRM_MODESET_LOCK_ALL_BEGIN/END, lock_all_ctx, per-object locks vs connection_mutex, stack_depot debugging | [curated] |
| commit-machinery.md | the helper commit engine: drm_atomic_helper_check (modeset+planes), prepare_planes/swap_state/commit_tail phase set (disables→planes→enables), struct drm_crtc_commit completions (flip_done/hw_done/cleanup_done) + refcounts, setup_commit/stall_checks (≤1 outstanding nonblock), wait_for_fences/dependencies/vblanks/flip_done, nonblock worker on system_unbound_wq, timeouts (10*HZ, 100ms); states the commit-path tracepoint split explicitly (generic helpers carry none; amdgpu_dm set → driver-ioctl-impl.md, intel pipe-update set → steady-state.md) | [prompt, split of "KMS atomic"] |

### ioctl/

| page | scope (anchor symbols) | tag |
|---|---|---|
| ioctl-dispatch.md | drm_ioctl→drm_ioctl_kernel: drm_ioctls[] (57 entries) + DRM_IOCTL_DEF + driver tables, enum drm_ioctl_flags permission model + drm_ioctl_permit, render-node gating, stack_kdata[128] copy strategy, getcap/setclientcap + all DRM_CLIENT_CAP_* (incl. new PLANE_COLOR_PIPELINE), new ioctls CLOSEFB/GEM_CHANGE_HANDLE/SET_CLIENT_NAME | [curated] |
| drm-file-events.md | struct drm_file lifecycle open→release: file_alloc/free, per-file object_idr/fbs/blobs, cap bools, event machinery (drm_pending_event, reserve/cancel/send, 4096-byte event_space, read/poll), client_id/fdinfo fields | [curated] |
| master-auth-lease.md | struct drm_master: is_master/was_master, SET/DROP_MASTER, magic map (getmagic/authmagic), drm_is_current_master; lease tree (lessor/lessees/leases idr), lease create/list/revoke ioctls, drm_lease_held/filter_crtcs gating object visibility | [curated] |
| addfb2.md | framebuffer creation uapi: struct drm_mode_fb_cmd2, drm_mode_addfb2/getfb2/rmfb/closefb + legacy addfb translation, framebuffer_check validation against format info, drm_internal_framebuffer_create→driver fb_create, dumb buffers (CREATE_DUMB + amdgpu/xe/i915 dumb_create) as the simplest producer | [curated] |
| legacy-over-atomic.md | legacy KMS entry points implemented over atomic: drm_mode_setcrtc, setplane, cursor/cursor2 (+hotspot), page_flip ioctl (+PAGE_FLIP_ASYNC), DIRTYFB, legacy gamma_set; how each builds an atomic commit internally | [curated] |
| kms-atomic-ioctl.md | DRM_IOCTL_MODE_ATOMIC decode: struct drm_mode_atomic layout, obj/prop array walk, drm_atomic_set_property routing per object type (incl. COLOROP), TEST_ONLY/NONBLOCK/ALLOW_MODESET/PAGE_FLIP_EVENT flags, IN_FENCE_FD/OUT_FENCE_PTR (prepare/complete_signaling), the retry/backoff loop, async-flip prop-change validation | [prompt] |
| display-pipeline-ioctl.md | the end-to-end uapi narrative to light a frame: GETRESOURCES→GETPLANERESOURCES→GETCONNECTOR/GETENCODER/GETCRTC enumeration, OBJ_GETPROPERTIES, ADDFB2, ATOMIC commit (or SETCRTC), page-flip loop; each step cites its owning page's entry point in one line | [prompt] |
| gem-handle-to-display.md | the handle-to-scanout chain: GEM handle in drm_mode_fb_cmd2 → drm_gem_object_lookup → fb->obj[] → plane fb assignment → the prepare_fb pin step cited in one line (the cross-driver pin comparison is gpuvm/scanout-pin.md's, boundary rule 12) → scanout address programming seam; fence attach along the way | [prompt] |
| driver-ioctl-impl.md | where KMS ioctls land per driver: amdgpu (amdgpu_mode_funcs fb_create amdgpu_display.c:1297, helper commit + amdgpu_dm_atomic_check/commit_tail, dm commit workers) vs i915/xe (intel_fb.c fb_create, own intel_atomic_commit + per-display modeset/flip workqueues), driver fops/ioctl-table wiring (amdgpu_drv.c, i915_driver.c, xe_device.c); owns the amdgpu_dm commit-path tracepoint set (trace_amdgpu_dm_atomic_commit_tail_begin amdgpu_dm.c:10883/_finish :11164, _atomic_check_begin :12497/_finish, _{connector,crtc,plane}_atomic_check) | [prompt] |

### timing/

| page | scope (anchor symbols) | tag |
|---|---|---|
| display-mode.md | struct drm_display_mode + uapi drm_mode_modeinfo: hdisplay/hsync_start/hsync_end/htotal + vertical twins (porch geometry figure), crtc_* adjusted copies + set_crtcinfo, DRM_MODE_FLAG_*, vrefresh math, mode lists/duplicate/equal/prune, umode↔kernel conversion + validation | [prompt] |
| vblank.md | struct drm_vblank_crtc machinery: refcount get/put + 5000ms disable timer (+per-CRTC config, immediate disable), seqlock-protected count/time, hw-counter wraparound (last/max_vblank_count), timestamping (framedur_ns, scanoutpos), on/off/reset, arm/send event, handle_vblank, WAIT_VBLANK + GET/QUEUE_SEQUENCE ioctls, drm_vblank_work (kthread worker); driver IRQ glue (amdgpu dm_crtc_high_irq/vupdate chain; intel_handle_vblank + xe dispatch), vblank tracepoints | [prompt] |
| vrr.md | variable refresh: vrr_capable connector prop + vrr_enabled CRTC prop, EDID monitor_range, amdgpu freesync module (build_vrr_params/handle_v_update, amdgpu_refresh_rate_track tracepoint) + i915/xe intel_vrr (transcoder timings, push), VRR vs vblank timestamping | [curated] |
| psr-panel-replay.md | eDP self-refresh: i915/xe intel_psr (compute/activate/pre-post_plane_update gating, invalidate/flush frontbuffer hooks) + amdgpu PSR (amdgpu_dm_psr) and Panel Replay (amdgpu_dm_replay); self_refresh_aware state; evidence note that generic drm_self_refresh_helper is DT-only and unused here | [curated] |
| dma-fence.md | struct dma_fence/dma_fence_ops: context/seqno/flags/error, init(+init64 new)/signal/wait/add_callback contracts, RCU freeing, chain (dma_fence_chain) + array + unwrap/merge, stub fences, deadline hint; the dma_fence tracepoint set; producer seam (amdgpu_fence/xe_hw_fence/i915_request one-liners) and display consumption (wait_for_fences, plane-state fence) | [prompt] |
| dma-resv.md | struct dma_resv as the BO lock: ww_mutex + fence list, enum dma_resv_usage classes (KERNEL/WRITE/READ/BOOKKEEP), lock/trylock/slow paths, reserve/add/replace fences, RCU iterators (iter_first/next retry), wait/test, implicit-sync semantics | [curated] |
| drm-syncobj.md | struct drm_syncobj: binary vs timeline (dma_fence_chain points), find/replace_fence, handle↔fd + sync_file bridge (sync_file.c folded here: create/merge/poll), wait/timeline_wait (5s submit-timeout), query/transfer/signal/eventfd ioctls, RCU fence slot | [prompt] |

### gem/

| page | scope (anchor symbols) | tag |
|---|---|---|
| gem-object.md | struct drm_gem_object + drm_gem_object_funcs: kref vs handle_count, object_init (shmem filp), size/resv/_resv, gpuva list, LRU helpers, free path; embedding relationships (ttm_bo.base, amdgpu_bo.tbo.base, xe_bo.ttm.base, i915 union) | [curated] |
| gem-handle.md | handle and name spaces: handle_create/delete/lookup over per-file object_idr, release_handle teardown, handle_count protocol (first/last handle vs object ref), flink/open global names (object_name_idr), GEM_CLOSE/FLINK/OPEN + new GEM_CHANGE_HANDLE ioctls | [curated] |
| gem-mmap.md | CPU mapping: drm_vma_offset_manager/node fake offsets (space constants), create_mmap_offset, vm_files access filtering + vma_node_revoke, drm_gem_mmap/mmap_obj dispatch to funcs->mmap/vm_ops, TTM fault path (ttm_bo_vm_fault(_reserved), prefault count, io_mem_reserve, pipelined-move wait), gem-ttm-helper shims, i915 mmap-offset modes | [curated] |
| prime-dmabuf.md | buffer sharing render↔display: handle↔fd ioctls, per-file import/export cache (rbtrees), self-import shortcut, drm_gem_prime_dmabuf_ops, dma_buf/ops/attachment lifecycle (attach/pin/map/cpu-access/vmap), sg-table helpers, importer move_notify (amdgpu_dma_buf_move_notify), driver dmabuf ops (amdgpu/xe/i915), the imported-BO-as-framebuffer path | [prompt] |

### ttm/

| page | scope (anchor symbols) | tag |
|---|---|---|
| ttm-device.md | struct ttm_device + ttm_device_funcs (the driver contract: tt create/populate/destroy, eviction_valuable, evict_flags, move, io_mem_reserve...), device_init (+new TTM_ALLOCATION_* alloc_flags), global sysman, lru_lock, delayed-destroy wq (max_active 16), amdgpu/xe/i915 ttm_device_funcs instances | [curated] |
| ttm-buffer-object.md | struct ttm_buffer_object over drm_gem_object: bo types (device/kernel/sg), init_reserved/init_validated, the validate placement loop (-EMULTIHOP bounce), pin/unpin vs LRU, own kref + delayed destroy/resurrect (individualized resv, BOOKKEEP wait), release notify | [curated] |
| ttm-resource-placement.md | ttm_resource/ttm_resource_manager/ttm_place/ttm_placement: mem types SYSTEM/TT/VRAM/PRIV (9 slots, 4 priorities), manager funcs (range/sys managers), LRU + ttm_lru_bulk_move (+cursor traversal), eviction (evict_flags→eviction_valuable→ttm_bo_evict), move fences (8), dmem-cgroup fields (new), domain mapping seam to driver pages | [curated] |
| ttm-tt.md | struct ttm_tt page backing: page_flags (SWAPPED/EXTERNAL/DECRYPTED/BACKED_UP...), create/populate/unpopulate + global swapout throttle, sg/dma_address, caching modes, NEW ttm_backup file-backed swap (ttm_backup.c, restore struct) | [curated] |
| ttm-pool.md | struct ttm_pool: per-caching/per-order page pools (NR_PAGE_ORDERS), alloc/free paths, WC/UC conversion cost, shrinker (round-robin ttm_pool_shrink), alloc_flags interplay, backup hooks | [curated] |
| ttm-move.md | moves: ttm_bo_handle_move_mem, ttm_bo_move_memcpy fallback, accel cleanup (ghost objects, pipelined evictions, KERNEL fences), multihop bounces; amdgpu_bo_move (VRAM↔GTT blits), xe_bo_move (xe_migrate), i915_ttm_move | [curated] |
| amdgpu-bo.md | struct amdgpu_bo over ttm: AMDGPU_GEM_DOMAIN_*→placements (max 3), create paths, pin (CPU-visible VRAM forcing for scanout), vram_mgr (drm_buddy-backed, 2MB blocks) + gtt_mgr, amdgpu_gem_object_funcs, dumb create, bo tracepoints | [curated] |
| xe-bo.md | struct xe_bo over ttm: placements/cpu_caching, create_locked, ggtt_node[], xe_ttm_vram_mgr (buddy)/sys/stolen managers, xe_bo_move + migrate, shrinker + ttm_backup wiring, xe_gem_object_funcs, dumb create, xe_bo tracepoints | [curated] |
| i915-gem-ttm.md | i915 object model: drm_i915_gem_object union with ttm_bo, ops structs, memory regions (intel_memory_region), TTM-backed region path (i915_gem_ttm.c), pin_to_display_plane (WT cache, scanout mark), mman offsets, shrinker notes, object tracepoints | [curated] |

### gpuvm/

| page | scope (anchor symbols) | tag |
|---|---|---|
| gpuvm-overview.md | generic drm_gpuvm/drm_gpuva/drm_gpuvm_bo: rb VA tree, kref model, lock protocols (RESV_PROTECTED vs IMMEDIATE_MODE + gpuva.lock), extobj/evict lists, sm_map/sm_unmap split-merge state machine + ops (map/remap/unmap), prepare/validate/resv_add_fence, deferred unlink (new); xe as the in-tree adopter, amdgpu/i915 explicitly not | [curated] |
| drm-mm.md | struct drm_mm/drm_mm_node range allocator: hole tracking (rb + stacks), insert modes, reserve/insert/remove, eviction scan roster (scan_init/add/remove_block), users (GEM vma manager, i915 GTT, xe ggtt) | [curated] |
| drm-buddy.md | struct drm_buddy allocator: NEW rb free_trees rework, block states/orders (max order 51), TOPDOWN/RANGE/CONTIGUOUS/CLEAR flags + clear_avail tracking, alloc_blocks/trim/free, amdgpu vram_mgr + xe vram_mgr as users; drm_suballoc (manager/fence-paced sub-allocation) folded here with amdgpu ring users | [curated] |
| amdgpu-vm.md | bespoke amdgpu_vm: rb va + amdgpu_bo_va(+mapping) with valids/invalids, vm_bo state machine (evicted/relocated/moved/idle/invalidated/done/freed lists + status_lock), eviction_lock+evicting, PT hierarchy (PDB3..PTB, amdgpu_vm_pt.c) + SDMA vs CPU update backends (update_funcs), update_range/bo_update, GEM_VA ioctl seam, VMID grab/flush (16 ids) + GART bind, user-queue eviction fences (new), amdgpu_vm tracepoints | [curated] |
| xe-vm.md | xe_vm over drm_gpuvm: xe_vma embedding drm_gpuva, VM_BIND ioctl machinery (bind ops prepare/run/fini/abort in xe_pt.c), vm->lock rwsem + resv, dma-fence vs LR/preempt-fence modes, rebind lists/worker, userptr via gpusvm notifier, xe_ggtt, xe vm/vma tracepoints | [curated] |
| xe-svm.md | shared virtual memory: drm_gpusvm core (init/range_get_pages, notifier_lock) + drm_pagemap device memory, xe_svm.c wiring, GPU fault-driven migration; xe-only at v7.0 (amdgpu does not use drm_gpusvm — its KFD SVM is out of scope) | [curated] |
| i915-address-space.md | i915_address_space over drm_mm: GGTT vs PPGTT (gen8 4-level) vs DPT classes, pte_encode/insert_entries hooks, vm->mutex + dual krefs, i915_vma lifecycle (embeds drm_mm_node; pin flags PIN_MASK, GLOBAL/LOCAL_BIND, SCANOUT bit), ggtt_pin, intel_dpt structure, vma bind tracepoints | [curated] |
| scanout-pin.md | why display pins instead of paging: amdgpu pinned CPU-visible VRAM (prepare_fb→amdgpu_bo_pin) vs i915/xe GGTT/DPT mapping (intel_plane_pin_fb→pin_to_ggtt/dpt; xe_fb_pin dpt/ggtt selection), pin lifetime across flips, relationship GEM⇄TTM⇄VM for a scanout buffer, unpin on cleanup_fb | [curated] |

### sched/

| page | scope (anchor symbols) | tag |
|---|---|---|
| gpu-scheduler.md | drm_sched: entity/rq/scheduler with credit model, job lifecycle (init/arm/push, dependencies xarray incl. resv deps), scheduled vs finished drm_sched_fence pair + parent hw fence, timeout/tdr, priorities (4), run/free workers; gpu_scheduler_trace.h events (MOVED at v7.0); amdgpu + xe as users, fence feed into display waits | [curated] |
| drm-exec.md | drm_exec multi-BO locking loop: ww ticket + objects array, until_all_locked retry idiom + contended/prelocked, prepare_obj/array + fence reservation, INTERRUPTIBLE_WAIT/IGNORE_DUPLICATES; standalone conditioned on the FULL user census (every amdgpu CS/GEM_VA and xe VM_BIND/exec call site enumerated per 7j/7m); recorded fallback if even the complete census yields a thin catalog relative to the row's scope (coverage-of-scope tripwire, guidelines/reference/measured-criteria.md): fold into gpu-scheduler.md | [curated] |

### Fold-in adjudications (topics that do NOT get pages)

sync_file → timing/drm-syncobj (fence-FD sibling; Area D thin flag). drm_vblank_work → timing/vblank. Client caps (getcap/setclientcap) → ioctl/ioctl-dispatch. Default state helpers + drm_private_obj → atomic/atomic-state. Dumb buffers → ioctl/addfb2 (+one-liners in driver BO pages). gem-ttm-helper → gem/gem-mmap. TTM eviction/LRU walk → ttm/ttm-resource-placement. drm-suballoc → gpuvm/drm-buddy. userptr → gpuvm/xe-vm + gpuvm/amdgpu-vm sections. amdgpu PT-update backends + VMID/GART → gpuvm/amdgpu-vm. DPT → gpuvm/i915-address-space (scanout-pin cites). intel_memory_region / amdgpu_gtt_mgr / xe stolen mgr → ttm driver BO pages. Broadcast RGB + HDR_OUTPUT_METADATA → pixel/color-gamut. Panel-orientation quirks + Content Protection property → kms/connector. Sharpness property → kms/crtc. FB_DAMAGE_CLIPS/damage helpers + scaling filter → kms/plane-composition. drm_rect/drm_fixed → kms/plane where used. Lease → ioctl/master-auth-lease (kept inside). drmm managed resources + debugfs/sysfs → core/drm-device. Fence producers (amdgpu_fence/xe_hw_fence/i915_request) + display fence consumption → timing/dma-fence sections (steady-state cites). MST dynamic-connector machinery → kms/connector (generic part only; MST itself is docs/dp/'s).

Fold-OUTs (out of campaign scope, recorded so nobody re-litigates): fbdev emulation + drm_client library (prompt bans fbdev; drm_client's in-tree consumer is the fbdev layer). MIPI-DSI (banned). tty (banned). DP protocol internals incl. DSC, HDCP transport, MST — docs/dp/ territory. drm_panel + drm_self_refresh_helper — DT-only, evidence in Area B/D digests. HDMI-specific infra (drm_scdc, HDMI CEC, drmm_connector_hdmi_init depth) — DP/eDP assumed. amdgpu KFD compute SVM — not a display construct.

### Projected total and tag census

77 pages: core/ 1, pixel/ 16 (9 + 7 formats), kms/ 18, atomic/ 3, ioctl/ 9, timing/ 7, gem/ 4, ttm/ 9, gpuvm/ 8, sched/ 2.
Tag census: 31 [prompt] (incl. 2 splits of the "KMS atomic" bullet), 46 [curated]; 3 of the curated rows (writeback, privacy-screen, panic) are flagged optional pending the user checkpoint.

### Overlap boundary rules (seam symbols named)

1. Format cluster: color-formats.md owns the format-info machinery and the IN_FORMATS/modifier advertising; each formats/* page owns only its families' layouts + `__drm_format_info` rows + driver-array membership; pitch-and-layout.md owns the pitch/offset/block math. Seam: struct drm_format_info (color-formats defines it in full; family pages reproduce their rows).
2. Color cluster: color-pipeline.md owns the per-CRTC blob pipeline AND struct intel_color_funcs with its commit-time hook order; colorop-pipeline.md owns the per-plane drm_colorop chain; gamma-degamma.md owns LUT data structures/validation and the LUT→HW extraction, citing intel_color_funcs.load_luts only as its consumer; ctm.md owns matrix formats/CSC; color-curve.md owns transfer-function semantics and curve math; color-gamut.md owns colorspace/encoding/range/HDR properties. Seams: struct drm_color_lut (gamma-degamma owns), intel_color_funcs.load_luts (color-pipeline owns the hook, gamma-degamma the data it loads), drm_colorop object machinery (colorop-pipeline owns; color-curve owns only enum drm_colorop_curve_1d_type semantics).
3. KMS base machinery: object-model.md owns drm_mode_object/IDR/refcount/lifetime models; property.md owns property+blob machinery; mode-config.md owns the registry+locks. Object pages (framebuffer/plane/crtc/encoder/connector) recap base machinery in at most one paragraph. Seam: drm_mode_object_add (object-model owns; object pages cite as a registration step).
4. plane.md owns object/state/formats/types; plane-composition.md owns the composition property set (alpha/rotation/zpos/blend/scaling/damage). Seam: drm_plane_state fields list (plane owns the struct tour; composition owns those properties' semantics + helpers).
5. connector.md owns the object/state/properties; edid.md owns parse→display_info AND the struct drm_display_info field tour (connector.md, pixel/bpc-and-bpp.md, pixel/color-gamut.md cite fields, never re-tour them); hotplug-detect.md owns status polling/HPD/probe. Seams: drm_edid_connector_update (edid owns), drm_helper_probe_single_connector_modes (hotplug-detect owns). All three stop at DPCD/AUX in one sentence (docs/dp/ boundary).
6. probe-init.md owns driver init ORDER + the registration split; object pages own per-object init APIs. Seam: drm_modeset_register_all.
7. modeset-pipeline.md is the cross-object callback narrative; atomic/commit-machinery.md owns generic commit plumbing; atomic/atomic-state.md owns state objects; ioctl/kms-atomic-ioctl.md owns uapi decode. Seam: drm_atomic_helper_commit_tail (commit-machinery owns its internals; modeset-pipeline uses it as the stage where object callbacks fire).
8. steady-state.md owns the flip repetition loop; timing/vblank.md owns vblank counting/events; timing/vrr.md and timing/psr-panel-replay.md own their mechanisms. Seam: drm_crtc_arm_vblank_event (vblank owns; steady-state cites).
9. ioctl cluster: ioctl-dispatch owns table/permissions; drm-file-events owns file+event lifecycle; master-auth-lease owns privilege; addfb2 owns fb_cmd2 validation→fb_create; kms-atomic-ioctl owns MODE_ATOMIC decode; display-pipeline-ioctl and gem-handle-to-display are end-to-end narratives citing owners one line each; driver-ioctl-impl owns the per-driver landing map. Seam: drm_internal_framebuffer_create (addfb2 owns).
10. GEM cluster: gem-object owns object+funcs+refcounts; gem-handle owns handle/name spaces; gem-mmap owns fake-offset+fault; prime-dmabuf owns sharing. Seams: drm_gem_object_release_handle (gem-handle), drm_vma_offset_node (gem-mmap).
11. TTM cluster: ttm-device owns the contract; ttm-buffer-object owns BO lifecycle incl. the validate loop's shape; ttm-resource-placement owns mem_space/manager/LRU/eviction internals; ttm-tt owns backing pages; ttm-pool owns pools; ttm-move owns move mechanics. Driver BO pages own domain→placement mapping + driver create/pin. Seams: ttm_bo_validate (bo page owns the loop; resource page owns ttm_bo_mem_space internals), ttm_bo_handle_move_mem (move owns).
12. GPUVM cluster: gpuvm-overview owns generic machinery; per-driver pages own their VMs; xe-svm owns gpusvm/pagemap; drm-mm/drm-buddy own allocators; scanout-pin owns the cross-driver pin comparison. Seams: drm_gpuvm_sm_map (overview owns; xe-vm cites), intel_plane_pin_fb + amdgpu_bo_pin (scanout-pin owns the comparison; ttm/ driver pages and gem-handle-to-display cite).
13. Sync cluster: dma-fence owns fence primitives + chain/array + producer/consumer seams; dma-resv owns the reservation object; drm-syncobj owns uapi sync handles + sync_file. Seams: dma_resv_add_fence (dma-resv owns), drm_syncobj_find_fence (drm-syncobj owns).
14. sched cluster: gpu-scheduler owns entity/job/fence; drm-exec owns the locking loop. Seam: drm_sched_job_add_resv_dependencies (scheduler owns; dma-resv cites).
15. House rule: every narrative page (modeset-pipeline, steady-state, display-pipeline-ioctl, gem-handle-to-display, scanout-pin) recaps any owned mechanism in ≤1 short paragraph and cites the owning page's anchor instead of re-walking it. Named applications: display-pipeline-ioctl.md holds the page-flip loop to a one-line cite of steady-state.md's anchor (drm_crtc_arm_vblank_event) since steady-state is written a batch later; gem-handle-to-display.md holds the pin comparison to one line (rule 12).

### Batch order (foundational → derived, ~4-5 pages per batch)

- B1: core/drm-device; kms/object-model; kms/mode-config; kms/property; pixel/color-formats
- B2: pixel/formats/rgb-8888, rgb-2101010, rgb-16161616, rgb565-and-legacy
- B3: pixel/formats/yuv-420-semiplanar, yuv-422-packed, yuv-444-packed
- B4: kms/framebuffer, kms/plane, kms/plane-composition, kms/crtc, pixel/pitch-and-layout
- B5: kms/encoder, kms/connector, kms/bridge, kms/edid
- B6: pixel/color-gamut, color-curve, gamma-degamma, ctm, bpc-and-bpp
- B7: pixel/color-pipeline, pixel/colorop-pipeline; kms/hotplug-detect, kms/probe-init
- B8: timing/display-mode, timing/vblank; atomic/modeset-locking, atomic/atomic-state
- B9: atomic/commit-machinery; ioctl/ioctl-dispatch, ioctl/drm-file-events, ioctl/master-auth-lease
- B10: gem/gem-object, gem/gem-handle, gem/gem-mmap; ioctl/addfb2
- B11: timing/dma-fence, timing/dma-resv, timing/drm-syncobj; sched/gpu-scheduler
- B12: ttm/ttm-device, ttm/ttm-buffer-object, ttm/ttm-resource-placement, ttm/ttm-tt
- B13: ttm/ttm-pool, ttm/ttm-move; gem/prime-dmabuf; sched/drm-exec
- B14: ttm/amdgpu-bo, ttm/xe-bo, ttm/i915-gem-ttm; gpuvm/drm-mm
- B15: gpuvm/drm-buddy, gpuvm/gpuvm-overview, gpuvm/amdgpu-vm, gpuvm/xe-vm
- B16: gpuvm/xe-svm, gpuvm/i915-address-space, gpuvm/scanout-pin; ioctl/legacy-over-atomic
- B17: ioctl/kms-atomic-ioctl, ioctl/display-pipeline-ioctl, ioctl/gem-handle-to-display, ioctl/driver-ioctl-impl
- B18: kms/modeset-pipeline, kms/steady-state; timing/vrr, timing/psr-panel-replay
- B19: kms/writeback, kms/privacy-screen, kms/panic (the optional tail — only if confirmed)

Ordering rationale: encodings and base object machinery first; object pages before the narratives that walk them; fence/BO/VM machinery before the handle-to-display, steady-state, and pin narratives; the four big end-to-end narrative pages (B17/B18) last so they cite verified anchors; optional peripherals close. (Amended: bpc-and-bpp B3→B6 and pitch-and-layout B3→B4 per review items 6-7, so their property/framebuffer anchors are written first or same-batch.)

### Adversarial review outcome (2026-07-12)

Reviewer checked ~30 scope anchors across all ten groups (incl. every v7.0-new symbol): zero anchor errors. Eight amendments returned; disposition:
1. ACCEPTED — commit-path tracepoint sets assigned to rows (amdgpu_dm set → driver-ioctl-impl; intel pipe-update set → steady-state; commit-machinery states the split).
2. ACCEPTED — gem-handle-to-display trimmed: pin comparison cited in one line, owned by scanout-pin (rule 12).
3. ACCEPTED — i915 LUT seam: color-pipeline owns intel_color_funcs + hook order; gamma-degamma owns LUT data/extraction (rule 2 updated).
4. ACCEPTED — struct drm_display_info field tour deeded to kms/edid.md; connector/bpc-and-bpp/color-gamut cite (rule 5 updated).
5. ACCEPTED WITH CONDITION — drm-exec stays standalone conditioned on the full user census per 7j/7m; recorded fallback: fold into gpu-scheduler.
6. ACCEPTED — bpc-and-bpp moved B3→B6 (its property/EDID anchors are B5).
7. ACCEPTED — pitch-and-layout moved B3→B4 (same batch as framebuffer; holds addfb2's framebuffer_check to a citation).
8. ACCEPTED AS BOUNDARY CLARIFICATION (no reorder) — display-pipeline-ioctl holds the flip loop to a one-line cite of steady-state's anchor (rule 15 named applications).

### Cross-subsystem boundary (fixed now, applies to every row)

The existing `docs/dp/` knowledge base (69 pages) owns the DP protocol layer: AUX channel, DPCD access/transport, every link-training phase (8b/10b and 128b/132b, LTTPR), MST end to end (topology, sideband, payload allocation, MST atomic state), and DP-level mode validation. `docs/drm/` pages stop at the seam where KMS hands off to `drivers/gpu/drm/display/drm_dp*` code: a drm/ page may name the DP helper entry it calls (e.g. connector detect reaching DPCD reads, encoder enable reaching link training) in one sentence, but never documents DP internals. MST connectors and DP tunneling are out of drm/ scope entirely.

## Execution & verification

- Pipeline (AMENDED 2026-07-12 to the redesigned skill flow): writer → orchestrator check per SKILL.md ("Modes"); substance is writer-owned end to end (parity table closed, mechanical exit suite run, evidence persisted into the dossier EVIDENCE section); the orchestrator re-runs the checks, adjudicates every residual itself, applies the fixes, and stamps WRITTEN → LINTED.
- Per-page procedure: passes 00-03 at write time (`guidelines/passes/`); every writer brief carries the boundary statements and the project bans below. The B1 writer briefs recorded earlier in Status predate the redesign; on resume, re-issue them from the current `guidelines/passes/02-write.md` template (adding the EVIDENCE persist directive).
- Project-specific writing bans (from prompt.md, on top of Gate A): no fbdev/tty mentions; no MIPI-DSI; no hedging; DP/eDP assumed as the output; DETAILS ordering generic → amdgpu → i915/xe (amdgpu always first); DCN35 named only for IP-specific code; tracepoints of the page's area explicitly covered; diagrams structural/spatial only.
- Write-time rules: every line number in this plan and in any draft is a hint — re-verify on disk at write time. Known corpus defect classes (audit pending): "vtable" (384), fbdev mentions (158), kerneldoc-elided (non-verbatim) excerpts corpus-wide.
- Save policy: pages land only under `docs/drm/<group>/`; no navigation-file edits; no git commits without explicit user go.

## Draft reuse map — DOWNGRADED TO REFERENCE (2026-07-12 user decision 3: write everything fresh)

This section is retained as the audit record of the prior-generation corpus (evidence for the CORRECTION entries above and for any future round that revisits reuse). It is NOT an execution input: writers consult neither draft corpus, and briefs carry no pointers into this section.

Corpus: the primary draft corpus (64 files); the secondary v6.19 corpus checked only for material absent from the primary. Slug mapping where the catalog renamed a topic: display-mode-timing→timing/display-mode, kms-atomic-uapi→ioctl/kms-atomic-ioctl, rgb565-and-indexed→formats/rgb565-and-legacy (adds XRGB1555), ttm-overview→ttm/ttm-device, mm/drm-buddy→gpuvm/drm-buddy (absorbs mm/drm-suballoc), edid/edid-parsing→kms/edid, atomic/state-helpers+private-objs→atomic/atomic-state, core/device-model→core/drm-device. core/fbdev-emulation.md is NOT carried (banned topic).

### Slice: kms/ + atomic/ + core/ + edid/ (18 files; audit complete, recorded 2026-07-12)

HEADLINE: ~100 spot checks — LINUX KERNEL catalog entries 100% accurate at v7.0 (structs, core fns, amdgpu/i915 driver fns alike). Only drift class: SUMMARY-prose field links collapsing to the enclosing struct's opening line (3 files: core/device-model up to 194 lines off for primary/render/driver_features; atomic/state-helpers mode_blob/degamma/ctm/gamma_lut; atomic/modeset-locking plane mutex + private-obj lock) — re-derive field-level anchors on reuse. Slice defects: abridged/elided non-verbatim blocks ~134 across 10/18 files, concentrated in the driver-comparison pages (kms-probe-init 23/28 blocks, steady-state 19/30, modeset-pipeline 19/28, connector 17/34); OTHER SOURCES fails 7n in 18/18 (rebuild from scratch); banned "contract"/"canonical" in 15/18 files incl. 6 headings ("Object-creation contract" ×4); depth ratio 0.21-1.00 all below the 1.0 floor (worst: plane 0.21, connector/crtc 0.24 — driver variants named but not walked); 1 missing provenance block (modeset-locking); 1 genuine label-colon (steady-state, the only confirmed one in 18 files). Raw grep counts for vtable (≤79)/arm (≤15)/bold/hedge resolve to ~zero genuine violations (filename substrings, arm-the-event verb, fenced kerneldoc).

Per-file verdicts (backbone unless noted; deltas only):
- kms/bridge.md (966) BACKBONE 5/5; elided 8/29; 3-panel topology figure (chain, state nesting, x86 direct-drive) reusable; bus-format negotiation walk strongest.
- kms/connector.md (1134) BACKBONE 6/6; elided 17/34 (highest ratio); list_iter section + property table strong; caller counts are prose numbers, not enumerated links — re-derive.
- kms/crtc.md (1121) BACKBONE 6/6 (field-level sub-cites verified exact); elided 13/29; color-mgmt + vblank subsections separable; 32-CRTC-cap fact verified.
- kms/encoder.md (923) BACKBONE 5/5; elided 6/29; update_connector_routing/check_valid_clones walk keep whole.
- kms/framebuffer.md (615) BACKBONE 4/4; elided 7/13; ADDFB2 creation walk best content; amdgpu/i915 sections thin prose (expand, not reuse).
- kms/kms-probe-init.md (1102) BACKBONE 6/6; elided 23/28 (heaviest); "fixed build order" + per-driver object-count tables + both probe walks carry near-verbatim after re-fetch.
- kms/mode-config.md (902) BACKBONE 5/5; elided 10/26; zero contract/canonical (only kms file); standard-properties table + IDR DETAILS reusable.
- kms/modeset-pipeline.md (1150) BACKBONE 4/4; elided 19/28; CHECK/COMMIT phase figure is code-flow (regenerate); disable-before/enable-after ordering cross-checked in both drivers — strongest parity material.
- kms/plane.md (849) MINE-SECTIONS-ONLY (worst ratio 0.21); 4/4; src/dst rectangle figure + check_plane_state walk keep; driver sections need real expansion.
- kms/property-blob.md (446) BACKBONE 5/5; zero elided; both figures near-production; cleanest small file.
- kms/steady-state.md (970) BACKBONE 5/5; elided 19/30; 1 genuine label-colon; flip-cycle figure is code-flow (regenerate); amdgpu ISR + i915 update_arm paths deepest parity DETAILS in corpus.
- kms/writeback.md (511) BACKBONE 5/5; zero elided; amdgpu-only fact verified; job-flow figure code-flow (regenerate), FIFO layout reusable.
- atomic/modeset-locking.md (422) BACKBONE; 4/4 API checks + 2 field-drift links to fix; the corpus's 1 missing-provenance block; LOCK_ALL macro walk solid.
- atomic/private-objs.md (590) BACKBONE 5/5; UAF-hazard timeline figure = single highest-value diagram in the set (flow-shaped; carry its facts + redraw); amdgpu-vs-intel_global_obj contrast keep. (Catalog folds this into atomic/atomic-state.)
- atomic/state-helpers.md (402) MINE-SECTIONS-ONLY; 3/3 API checks + 4 field-drift cites; 5 "contract" hits incl. its own headings; duplicates per-object pages' helper subsections — supports the catalog fold into atomic/atomic-state; kept-vs-cleared field table generalizes.
- core/device-model.md (654) BACKBONE 4/4 + 3 field-drift links; 3 figures (2 flow-shaped, redraw); drmm/devres DETAILS strong.
- core/fbdev-emulation.md (687) IGNORE (banned topic); only the generic drm_client plumbing (~20-25%) is salvageable and the campaign's fold-out adjudication (drm_client skipped: its in-tree consumer is the banned layer) stands.
- edid/edid-parsing.md (1169) BACKBONE 6/6; zero elided; priority-order mode list + CTA-861 parse chain strongest reuse; byte-offset layout figure reusable, call-chain figure regenerate; VESA E-EDID/CTA-861 belong in SPECIFICATIONS.

### Slice: ttm/ + gem/ + gpuvm/ + sched/ + mm/ (22 files; audit complete, recorded 2026-07-12)

HEADLINE: staleness 0/115 spot checks — symbol/line cites exact at v7.0 (apparent drifts were kerneldoc-comment matching artifacts, resolved by direct read). Slice-wide defects: kerneldoc-elided non-verbatim excerpts 44 across 15/22 files (worst: gpuvm-overview 7, xe-vm 7, ttm-overview 6); missing provenance comment 1 (drm-exec INTERFACES block); banned Why/How heading 1 (ttm-move "How the move fence reaches dma_resv"); banned word "canonical" in roughly half the files (sweep on reuse); genuine boldface/colon-label/vtable/arm-metaphor/fbdev/tty/MIPI/DSI all ZERO (raw greps over-counted via `/**` openers, verb-sense "arm", and drm_sched_job_arm symbol names). Depth uniformly below standard: 0.40-0.92 c-blocks per catalog entry (all below the 1.0 floor; corpus total 20,155 lines ≈ 62% of the 22-page aggregate floor). Figures: 28 total; ~22 structural/topology/layout reusable near-verbatim (drm-buddy's packed-u64 header bitfield is the single best 7h calibration figure in the corpus); ~6 are code-flow shape and must become prose + salvaged structural fragments (ttm-move fig, gem-ttm-helper fig2, drm-exec fig2, drm-suballoc fig2, gpu-scheduler fig2, gem-mmap top panel). OTHER SOURCES fail 7n uniformly (generic links, no lore/commit trailers) — rebuild everywhere. No topic should be dropped; scanout-pin-vm needs its boundary against kms/plane checked (handled: boundary rule 12).

Per-file verdicts (all 22 BACKBONE-REUSABLE; deltas only):
- ttm/ttm-buffer-object.md (855) 6/6 checks; elided 1; embedding figure reusable.
- ttm/ttm-eviction-lru.md (1110) 6/6; elided 2; 54-entry catalog, richest eviction walk (evict_first/alloc/cb, bulk move) — feeds ttm-resource-placement per catalog merge.
- ttm/ttm-move.md (978) 6/6; elided 1; 1 banned heading; its only figure is pure call-flow (redraw); ghost/pipeline DETAILS strong.
- ttm/ttm-overview.md (848) 6/6; elided 6 (re-fetch funcs structs); three-driver init tour good spine → feeds ttm-device.
- ttm/ttm-pool.md (542) 6/6; ZERO defects; 2 reusable figures (freelist grid, shrinker topology); least rework in corpus.
- ttm/ttm-resource-placement.md (980) 6/6; elided 2; mem_type table + buddy seam pointers good.
- ttm/ttm-tt.md (1098) 5/5; elided 3; caching/page-flags catalog + amdgpu userptr/GART + xe backup rich.
- gem/gem-handle.md (812) 6/6 (incl. ioctl-table line-range cite); elided 1; kref-vs-handle_count DETAILS is the 7j model.
- gem/gem-mmap.md (1152) 6/6; elided 1; split figure: keep embedding panel, prose-ify pipeline panel; 4-driver fault comparison strongest in corpus.
- gem/gem-object.md (851) 6/6; elided 3; the base-class page all embedding claims depend on — consistency seam to check first.
- gem/gem-prime-dmabuf.md (1137) 6/6; elided 3; exporter/importer topology figure reusable; ADDFB2-import seam noted.
- gem/gem-ttm-helper.md (518) 5/5; elided 0; fig2 call-flow (redraw); vma-owns-one-ref claim needs 7o re-derivation. (Catalog folds this into gem/gem-mmap.)
- gpuvm/amdgpu-vm.md (1179) 5/5; elided 1; radix-tree figure reusable; CPU-vs-SDMA backend split + "amdgpu does not use drm_gpuvm" seam fact carry over.
- gpuvm/drm-mm.md (1005) 5/5; elided 3; node/hole interval figure is textbook 7g; eviction-roster DETAILS extend.
- gpuvm/gpuvm-overview.md (873) 5/5; elided 7 (heaviest, re-fetch first); 60-entry catalog; sm_map/sm_unmap DETAILS deepest algorithmic material in group.
- gpuvm/i915-ppgtt.md (982) 6/6; elided 0 (cleanest); gen8 PTE-encode depth is the group's only hardware-facing material.
- gpuvm/scanout-pin-vm.md (987) 6/6 (confirmed intel_plane_pin_fb exists TWICE: i915 intel_fb_pin.c:263 and xe xe_fb_pin.c:419 — disambiguate when citing); elided 3; two-lane render-vs-scanout figure reusable.
- gpuvm/xe-vm.md (866) 5/5; elided 7 (heaviest, re-fetch first); VM_BIND→gpuva-ops→PT walk fullest ioctl-to-hardware trace in corpus.
- sched/drm-exec.md (656) 5/5; elided 0; 1 missing-provenance block + "canonical" use; fig2 wound-wait scenario → prose.
- sched/gpu-scheduler.md (1334) 6/6; elided 0; credit flow-control + timeout/reset DETAILS richest async material; fence-timeline fig2 redraw.
- mm/drm-buddy.md (958) 5/5; ZERO defects; header-bitfield + rb-forest figures both reusable.
- mm/drm-suballoc.md (434) 5/5; ZERO defects; flist[] figure reusable, fig2 retry loop → prose. (Catalog folds this into gpuvm/drm-buddy.)

### Slice: pixel/ + ioctl/ + timing/ (24 files; audit complete, recorded 2026-07-12)

HEADLINE: staleness rate 0% — every one of ~60 spot-checked symbol/line citations (incl. deep DETAILS ones) landed exactly at v7.0. All 395 fenced c blocks carry `/* path:line */` provenance. Corpus-wide defects for this slice: boldface 0, prose-colon ~0, hedging ~5 mild in 4 files, genuine "vtable" 0 (25 raw hits = filename `drm_modeset_helper_vtables.h`), genuine branch-metaphor "arm" 6 in 3 files (bpc-and-bpp 4, yuv-422-packed 1, yuv-444-packed 1), banned "contract" ~10 in 6 files, "kerneldoc elided" non-verbatim excerpts ~29 across 11/24 files (worst: gem-handle-to-display 6, dma-fence 4), fbdev/tty/MIPI/DSI 0, missing provenance 0. Every lead figure (1 per file, 24 total) is a legitimate structural/topology/byte-layout/waveform/swimlane pattern — none is a banned call-graph. OTHER SOURCES fail 7n corpus-wide (Wikipedia/LWN/YouTube; rebuild per 7n everywhere).

Per-file verdicts (backbone = reuse skeleton+facts, extend to standard; mine = selected sections only):
- pixel/bpc-and-bpp.md (677) BACKBONE; 5/5 spot-checks; 4 genuine arm; MAX_BPC INTERFACES table reusable; silent on colorop pipeline.
- pixel/color-curve.md (316) BACKBONE; 4/4; amdgpu_transfer_function→DC mapping table reusable; no drm_colorop_curve_1d_type.
- pixel/color-formats.md (1088) BACKBONE; 4/4; 3 elided structs to re-collect verbatim; __drm_format_info walk is the family backbone.
- pixel/color-gamut.md (331) BACKBONE; 4/4; cleanest file; property tables + input_csc_matrix[] table reusable; OTHER SOURCES all Wikipedia.
- pixel/color-pipeline.md (496) BACKBONE; 4/4; 12 arm hits all exempt (symbol names/verb); legacy-CRTC-pipeline only — colorop section is a real gap.
- pixel/ctm.md (342) BACKBONE; 3/3; REGISTERS coefficient table reusable; no CTM_3X4/colorop.
- pixel/gamma-degamma.md (410) BACKBONE; 3/3; LUT-size table reusable; colorop 1D_LUT/1D_CURVE absent.
- pixel/pitch-and-layout.md (572) BACKBONE; 4/4; 1 elided (drm_mode_fb_cmd2); amdgpu block-geometry switch + intel_tile_width_bytes table carry forward.
- pixel/formats/* (7 files, 150-208 lines, 4-6 c-blocks each) ALL MINE-SECTIONS-ONLY; spot-checks hit; per-format byte/channel-layout figure present in every one (reusable); rgb-8888 deepest (alpha/blend table feeds siblings); yuv-422/444 carry 1 genuine arm each; rgb565-and-indexed cleanest.
- ioctl/ioctl-dispatch.md (801) BACKBONE; 5/5; 3 elided; four-flag permission table + core/driver table-split table reusable.
- ioctl/driver-ioctl-impl.md (903) BACKBONE; 4/4; 2 elided; 2 "contract" headings to rename; amdgpu-vs-i915 hook comparison table is load-bearing.
- ioctl/kms-atomic-uapi.md (1056) BACKBONE; 3/3; 2 elided; flags table + set_property switch reusable; 2 editorializing phrases.
- ioctl/display-pipeline-ioctl.md (1135) BACKBONE; 3/3; 3 elided; swimlane figure legit; ioctl→handler→struct INTERFACES table high-value.
- ioctl/gem-handle-to-display.md (1159) BACKBONE; 4/4; 6 elided (worst; drm_gem_object/drm_file abridged — re-collect); fb_create/prepare_fb hook table excellent.
- timing/display-mode-timing.md (796) BACKBONE; 4/4; 1 elided; timing waveform figure canonical; 1 banned heading ("Where modes originate") to rename.
- timing/dma-fence.md (927) BACKBONE; 4/4; 4 elided; 3 "contract"; dma_fence_ops requirement table + dma_resv_usage ordering table reusable; xe side thin — expand not reuse.
- timing/drm-syncobj.md (867) BACKBONE; 4/4; 2 elided; SYNCOBJ ioctl/feature table + wait/import flags table reusable.
- timing/vblank.md (1142) BACKBONE; 10/10 (strongest skeleton in the whole corpus); 2 elided; 17 arm hits all legitimate; refcount-threshold table + four-hook comparison table exemplary.

SECONDARY CORPUS finding (its v6.19 color drafts): every color file in the secondary corpus carries a "Per-Plane Colorop Pipeline" section (drm_colorop/drm_colorop_state/drm_colorop_type/drm_plane_colorop_*_init) that the primary draft corpus lacks entirely; confirmed present in the real v7.0 tree. Mine that skeleton for pixel/colorop-pipeline.md with every symbol re-verified at v7.0. Its OTHER SOURCES are YouTube explainers — fail 7n, replace.

Write-time consequences for this slice: re-collect every "kerneldoc elided" excerpt verbatim from disk; rename "contract" headings; reword the 6 genuine arm uses; treat all draft line numbers as hints (0% observed drift but the rule stands).
