// XVCpanel — Domain Warp Shader (Processing GLSL)

#ifdef GL_ES
precision mediump float;
#endif

#define PROCESSING_TEXTURE_SHADER

uniform sampler2D texture;
uniform vec2 texOffset;
uniform float time;
uniform vec2 resolution;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    for (int i = 0; i < 6; i++) {
        v += a * noise(p);
        p = p * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = gl_FragCoord.xy / resolution.xy;
    vec2 p = uv * 3.0;
    float t = time * 0.15;

    vec2 q = vec2(fbm(p + vec2(0.0, 0.0) + t),
                   fbm(p + vec2(5.2, 1.3) + t * 0.7));
    vec2 r = vec2(fbm(p + 4.0 * q + vec2(1.7, 9.2) + t * 0.5),
                   fbm(p + 4.0 * q + vec2(8.3, 2.8) + t * 0.3));
    float f = fbm(p + 4.0 * r);

    vec3 c1 = vec3(0.1, 0.2, 0.4);
    vec3 c2 = vec3(0.8, 0.2, 0.5);
    vec3 c3 = vec3(0.1, 0.8, 0.6);
    vec3 c4 = vec3(0.9, 0.6, 0.1);

    vec3 col = mix(c1, c2, clamp(f * f * 2.0, 0.0, 1.0));
    col = mix(col, c3, clamp(length(q), 0.0, 1.0));
    col = mix(col, c4, clamp(length(r.x), 0.0, 1.0));
    col *= 0.8 + 0.4 * f;

    gl_FragColor = vec4(col, 1.0);
}
