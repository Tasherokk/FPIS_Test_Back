from django.contrib.auth import authenticate
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.exceptions import Throttled
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from .models import Subject, Question, Answer, MatchingPair, TestResult, SubjectResult
from .serializers import SubjectSerializer, TestResultSerializer
import random

from .throttles import SubmitAnswersThrottle, GenerateTestThrottle


class GenerateTestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [GenerateTestThrottle]

    def post(self, request):
        try:
            selected_subjects = request.data.get('selected_subjects', [])
            default_subjects = ['HIS', 'RL', 'ML', ]
            all_subjects = default_subjects + selected_subjects

            test_data = []

            for subject_code in all_subjects:
                variants = Subject.objects.filter(name=subject_code, is_active=True).values_list('variant', flat=True)
                if not variants:
                    return Response(
                        {'error': f'No variants for subject {subject_code}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                variant = random.choice(variants)
                subject = Subject.objects.get(name=subject_code, variant=variant)
                serializer = SubjectSerializer(subject)
                test_data.append(serializer.data)

            return Response({'test': test_data}, status=status.HTTP_200_OK)

        except Throttled as e:
            wait_time = e.wait
            response = Response(
                {"error": "Rate limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            if wait_time is not None:
                response.headers['Retry-After'] = str(wait_time)
                print("Retry-After header set to:", wait_time)
            return response


class SubmitAnswersView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SubmitAnswersThrottle]

    def post(self, request):
        answers = request.data.get('answers', {})
        if not answers:
            return Response({'error': 'No answers provided.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        total_score = 0
        test_result = TestResult.objects.create(user=user, total_score=0)

        # Здесь будем сохранять информацию о правильных ответах
        # Данные вида: { subject_id: { question_id: {...}, ...}, ... }
        correct_answers_dict = {}

        for subject_id_str, subject_answers in answers.items():
            try:
                subject_id = int(subject_id_str)
                subject = Subject.objects.get(id=subject_id)
            except (ValueError, Subject.DoesNotExist):
                # Skip invalid subject IDs
                continue

            subject_score = 0
            correct_answers_dict[subject_id] = {}

            for question_id_str, user_answers in subject_answers.items():
                try:
                    question_id = int(question_id_str)
                    question = Question.objects.get(id=question_id)
                except (ValueError, Question.DoesNotExist):
                    # Skip invalid question IDs
                    continue

                # Подготовим структуру для хранения "правильных ответов" по каждому question_id
                correct_answers_dict[subject_id][question_id] = {
                    'question_type': question.question_type,
                    'correct_answers': [],
                }

                if question.question_type == 'SC':
                    # Найдём правильный ответ (их максимум один в SC)
                    correct_answer = question.answers.filter(is_correct=True).first()
                    if correct_answer:
                        correct_answers_dict[subject_id][question_id]['correct_answers'] = [correct_answer.id]

                    if not user_answers:
                        # No answer selected
                        pass  # Treat as incorrect
                    else:
                        try:
                            user_answer_id = int(user_answers[0])
                            if correct_answer and correct_answer.id == user_answer_id:
                                subject_score += 1
                        except (ValueError, IndexError):
                            # Invalid answer format
                            pass  # Treat as incorrect

                elif question.question_type == 'MC':
                    # Найдём все правильные ответы (их может быть несколько)
                    correct_answer_ids = set(question.answers.filter(is_correct=True).values_list('id', flat=True))
                    correct_answers_dict[subject_id][question_id]['correct_answers'] = list(correct_answer_ids)

                    if not user_answers:
                        # No answers selected
                        pass  # Treat as incorrect
                    else:
                        try:
                            user_answer_ids = set(map(int, user_answers))
                            if user_answer_ids == correct_answer_ids:
                                subject_score += 2
                        except ValueError:
                            # Invalid answer format
                            pass  # Treat as incorrect

                elif question.question_type == 'MT':
                    # Предположим, что в модели один MatchingPair на вопрос (как у вас в примере)
                    matching_pair = question.matching_pairs.first()
                    if matching_pair:
                        # Сохраняем правильную комбинацию
                        correct_answers_dict[subject_id][question_id]['correct_answers'] = {
                            'left_side_1': matching_pair.correct_for_left_1,
                            'left_side_2': matching_pair.correct_for_left_2
                        }


                    left_side_1_value = user_answers.get('left_side_1')
                    left_side_2_value = user_answers.get('left_side_2')

                    # Check if any matching pair values are missing or empty
                    if not left_side_1_value or not left_side_2_value:
                        # One or more matches not selected
                        pass  # Treat as incorrect
                    else:
                        try:
                            left_side_1_value = int(left_side_1_value)
                            left_side_2_value = int(left_side_2_value)
                        except ValueError:
                            # Invalid integer conversion
                            pass  # Treat as incorrect
                        else:
                            if matching_pair and (
                                matching_pair.correct_for_left_1 == left_side_1_value and
                                matching_pair.correct_for_left_2 == left_side_2_value
                            ):
                                subject_score += 2


            total_score += subject_score
            SubjectResult.objects.create(test_result=test_result, subject=subject, score=subject_score)

        test_result.total_score = total_score
        test_result.save()

        serializer = TestResultSerializer(test_result)

        # Дополнительно вложим correct_answers_dict, чтобы фронт понимал, какие ответы верные
        response_data = serializer.data
        response_data['correct_answers'] = correct_answers_dict

        return Response(response_data, status=status.HTTP_200_OK)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        iin = request.data.get('iin')
        password = request.data.get('password')
        user = authenticate(request, iin=iin, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'iin': user.iin,
                'full_name': user.full_name
            }, status=status.HTTP_200_OK)

        return Response({"error": "Неверный ИИН"}, status=status.HTTP_400_BAD_REQUEST)