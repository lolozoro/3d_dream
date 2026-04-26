import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

/**
 * ⚠️ 此 Edge Function 已改为本地后端的代理转发层。
 *
 * 项目架构原则：所有数据处理（包括 AI 模型调用）均由前端 → 本地后端处理，
 * 后端统一通过 .env 中的 DASHSCOPE_API_KEY 管理模型调用，后端管理数据库。
 *
 * 此函数不再直接调用任何外部 AI Gateway，仅将请求转发到配置的本地后端地址。
 */

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { headers: corsHeaders });
  }

  try {
    const body = await req.json();
    const LOCAL_BACKEND_URL = Deno.env.get("LOCAL_BACKEND_URL") || "http://host.docker.internal:8000";

    // 根据请求体判断目标端点：
    // - 包含 instruction + mindmap -> /mindmap/update
    // - 包含 messages + mindmap -> /chat
    const isUpdate = body.instruction !== undefined && body.mindmap !== undefined;
    const endpoint = isUpdate ? "/mindmap/update" : "/chat";
    const targetUrl = `${LOCAL_BACKEND_URL.replace(/\/$/, "")}${endpoint}`;

    const response = await fetch(targetUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const text = await response.text();
      console.error("Backend proxy error:", response.status, text);
      return new Response(
        JSON.stringify({ error: "后端服务异常，请检查本地后端是否运行" }),
        {
          status: 502,
          headers: { ...corsHeaders, "Content-Type": "application/json" },
        },
      );
    }

    const data = await response.json();

    // 统一返回格式（兼容前端旧接口）
    if (isUpdate) {
      return new Response(
        JSON.stringify({
          reply: data.explanation || "脑图已更新。",
          updatedMindmap: data.mindmap || null,
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    } else {
      return new Response(
        JSON.stringify({
          reply: data.reply || data.answer || "",
          updatedMindmap: data.updated_mindmap || data.updatedMindmap || null,
        }),
        { headers: { ...corsHeaders, "Content-Type": "application/json" } },
      );
    }
  } catch (e) {
    console.error("mindmap-chat proxy error:", e);
    return new Response(
      JSON.stringify({ error: e instanceof Error ? e.message : "Unknown" }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } },
    );
  }
});
