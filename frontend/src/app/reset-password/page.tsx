"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Label } from "@/components/ui/label";
import { LayoutDashboard, Eye, EyeOff, ArrowLeft } from "lucide-react";
import Link from "next/link";

const requestResetSchema = z.object({
  email: z.string().email("올바른 이메일 주소를 입력해주세요"),
});

const resetPasswordSchema = z.object({
  password: z.string().min(8, "비밀번호는 최소 8글자 이상이어야 합니다"),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "비밀번호가 일치하지 않습니다",
  path: ["confirmPassword"],
});

type RequestResetForm = z.infer<typeof requestResetSchema>;
type ResetPasswordForm = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  
  const isResetMode = !!token;
  
  const requestForm = useForm<RequestResetForm>({
    resolver: zodResolver(requestResetSchema),
  });
  
  const resetForm = useForm<ResetPasswordForm>({
    resolver: zodResolver(resetPasswordSchema),
  });

  const onRequestReset = async (data: RequestResetForm) => {
    setError("");
    setIsLoading(true);

    try {
      // TODO: Implement password reset request API call
      // const response = await typeSafeApiClient.requestPasswordReset(data.email);
      
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setEmailSent(true);
      
    } catch (err) {
      setError("비밀번호 재설정 요청 중 오류가 발생했습니다. 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  const onResetPassword = async (data: ResetPasswordForm) => {
    setError("");
    setIsLoading(true);

    try {
      // TODO: Implement password reset API call
      // const response = await typeSafeApiClient.resetPassword(token, data.password);
      
      // Simulate API call for now
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess(true);
      
      // Redirect to login after successful reset
      setTimeout(() => {
        router.push("/login?reset=true");
      }, 2000);
      
    } catch (err) {
      setError("비밀번호 재설정 중 오류가 발생했습니다. 다시 시도해주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="w-full max-w-md space-y-8">
          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="mx-auto w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold mb-2">비밀번호가 변경되었습니다!</h2>
                <p className="text-muted-foreground">
                  새 비밀번호로 로그인하실 수 있습니다.<br />
                  로그인 페이지로 이동합니다...
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  if (emailSent && !isResetMode) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <div className="mx-auto w-16 h-16 bg-primary rounded-lg flex items-center justify-center mb-4">
              <LayoutDashboard className="w-8 h-8 text-primary-foreground" />
            </div>
            <h1 className="text-3xl font-bold">GA4 관리자</h1>
          </div>

          <Card>
            <CardContent className="pt-6">
              <div className="text-center">
                <div className="mx-auto w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mb-4">
                  <svg className="w-8 h-8 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.01 4.455A2 2 0 0011 14.455V16a2 2 0 004 0v-5.01l4-2.97" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold mb-2">이메일을 확인해주세요</h2>
                <p className="text-muted-foreground mb-4">
                  비밀번호 재설정 링크를 이메일로 발송했습니다.<br />
                  이메일을 확인하고 링크를 클릭해주세요.
                </p>
                <Link href="/login">
                  <Button variant="outline" className="w-full">
                    <ArrowLeft className="w-4 h-4 mr-2" />
                    로그인 페이지로 돌아가기
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="mx-auto w-16 h-16 bg-primary rounded-lg flex items-center justify-center mb-4">
            <LayoutDashboard className="w-8 h-8 text-primary-foreground" />
          </div>
          <h1 className="text-3xl font-bold">GA4 관리자</h1>
          <p className="text-muted-foreground mt-2">
            {isResetMode ? "새 비밀번호를 설정하세요" : "비밀번호를 재설정하세요"}
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>
              {isResetMode ? "비밀번호 재설정" : "비밀번호 재설정 요청"}
            </CardTitle>
            <CardDescription>
              {isResetMode 
                ? "새로운 비밀번호를 입력해주세요" 
                : "등록된 이메일 주소로 재설정 링크를 보내드립니다"
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isResetMode ? (
              <form onSubmit={resetForm.handleSubmit(onResetPassword)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="password">새 비밀번호 *</Label>
                  <div className="relative">
                    <Input
                      id="password"
                      type={showPassword ? "text" : "password"}
                      placeholder="8글자 이상 입력하세요"
                      disabled={isLoading}
                      {...resetForm.register("password")}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowPassword(!showPassword)}
                      disabled={isLoading}
                    >
                      {showPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {resetForm.formState.errors.password && (
                    <p className="text-sm text-destructive">{resetForm.formState.errors.password.message}</p>
                  )}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">비밀번호 확인 *</Label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="비밀번호를 다시 입력하세요"
                      disabled={isLoading}
                      {...resetForm.register("confirmPassword")}
                    />
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      disabled={isLoading}
                    >
                      {showConfirmPassword ? (
                        <EyeOff className="h-4 w-4" />
                      ) : (
                        <Eye className="h-4 w-4" />
                      )}
                    </Button>
                  </div>
                  {resetForm.formState.errors.confirmPassword && (
                    <p className="text-sm text-destructive">{resetForm.formState.errors.confirmPassword.message}</p>
                  )}
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={isLoading}
                >
                  {isLoading ? "비밀번호 변경 중..." : "비밀번호 변경"}
                </Button>
              </form>
            ) : (
              <form onSubmit={requestForm.handleSubmit(onRequestReset)} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email">이메일 주소</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="admin@example.com"
                    disabled={isLoading}
                    {...requestForm.register("email")}
                  />
                  {requestForm.formState.errors.email && (
                    <p className="text-sm text-destructive">{requestForm.formState.errors.email.message}</p>
                  )}
                </div>

                {error && (
                  <Alert variant="destructive">
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <Button 
                  type="submit" 
                  className="w-full" 
                  disabled={isLoading}
                >
                  {isLoading ? "요청 중..." : "재설정 링크 발송"}
                </Button>
              </form>
            )}

            <div className="mt-6 text-center">
              <Link href="/login" className="inline-flex items-center text-sm text-muted-foreground hover:text-primary">
                <ArrowLeft className="w-4 h-4 mr-1" />
                로그인 페이지로 돌아가기
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}