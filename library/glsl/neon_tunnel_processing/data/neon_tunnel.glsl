// XVCpanel - Neon Tunnel (Processing GLSL)

#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 resolution;
uniform float time;

void main() {
    vec2 uv = (2.0 * gl_FragCoord.xy - resolution.xy) / resolution.y;
    float angle = atan(uv.y, uv.x);
    float depth = 1.0 / max(length(uv), 0.001);
    float rings = sin(depth * 7.0 - time * 3.0);
    float rails = sin(angle * 10.0 + time * 0.6);
    float glow = pow(max(rings, 0.0), 12.0) + pow(max(rails, 0.0), 18.0) * 0.35;
    vec3 color = vec3(0.08, 0.01, 0.20) + glow * vec3(0.15, 0.85, 1.0);
    color += pow(max(sin(depth * 3.5 - time), 0.0), 20.0) * vec3(1.0, 0.05, 0.55);
    gl_FragColor = vec4(color, 1.0);
}
